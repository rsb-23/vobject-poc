"""
Compare VTODOs and VEVENTs in two iCalendar sources.
"""

from argparse import ArgumentParser

import vobject

from .compatibility import deprecated


def get_sort_key(component):
    def get_uid(component):
        return component.getChildValue("uid", "")

    # it's not quite as simple as getUID, need to account for recurrenceID and sequence

    def get_sequence(component) -> str:
        sequence = component.getChildValue("sequence", 0)
        return f"{int(sequence):05d}"

    def get_recurrence_id(component):
        recurrence_id = component.getChildValue("recurrence_id", None)
        if recurrence_id is None:
            return "0000-00-00"
        else:
            return recurrence_id.isoformat()

    return get_uid(component) + get_sequence(component) + get_recurrence_id(component)


def sort_by_uid(components):
    return sorted(components, key=get_sort_key)


def delete_extraneous(component, ignore_dtstamp=False):
    """
    Recursively walk the component's children, deleting extraneous details like
    X-VOBJ-ORIGINAL-TZID.
    """
    for comp in component.components():
        delete_extraneous(comp, ignore_dtstamp)
    for line in component.lines():
        if "X-VOBJ-ORIGINAL-TZID" in line.params:
            del line.params["X-VOBJ-ORIGINAL-TZID"]
    if ignore_dtstamp and hasattr(component, "dtstamp_list"):
        del component.dtstamp_list


def diff(left, right):
    """
    Take two VCALENDAR components, compare VEVENTs and VTODOs in them,
    return a list of object pairs containing just UID and the bits
    that didn't match, using None for objects that weren't present in one
    version or the other.

    When there are multiple ContentLines in one VEVENT, for instance many
    DESCRIPTION lines, such lines original order is assumed to be
    meaningful.  Order is also preserved when comparing (the unlikely case
    of) multiple parameters of the same type in a ContentLine

    """

    def process_component_lists(left_list, right_list):
        output = []
        right_index = 0
        right_list_size = len(right_list)

        for comp in left_list:
            if right_index >= right_list_size:
                output.append((comp, None))
            else:
                left_key = get_sort_key(comp)
                right_comp = right_list[right_index]
                right_key = get_sort_key(right_comp)
                while left_key > right_key:
                    output.append((None, right_comp))
                    right_index += 1
                    if right_index >= right_list_size:
                        output.append((comp, None))
                        break
                    right_comp = right_list[right_index]
                    right_key = get_sort_key(right_comp)

                if left_key < right_key:
                    output.append((comp, None))
                elif left_key == right_key:
                    right_index += 1
                    match_result = process_component_pair(comp, right_comp)
                    if match_result is not None:
                        output.append(match_result)

        return output

    def new_component(name, body):  # pylint:disable=unused-variable
        if body is None:
            return None
        c = vobject.base.Component(name)
        c.behavior = vobject.base.getBehavior(name)
        c.isNative = True
        return c

    def process_component_pair(left_comp, right_comp):
        """
        Return None if a match, or a pair of components including UIDs and
        any differing children.

        """
        left_child_keys = left_comp.contents.keys()
        right_child_keys = right_comp.contents.keys()

        different_content_lines = []
        different_components = {}

        for key in left_child_keys:
            right_list = right_comp.contents.get(key, [])
            if isinstance(left_comp.contents[key][0], vobject.base.Component):
                comp_difference = process_component_lists(left_comp.contents[key], right_list)
                if len(comp_difference) > 0:
                    different_components[key] = comp_difference

            elif left_comp.contents[key] != right_list:
                different_content_lines.append((left_comp.contents[key], right_list))

        for key in right_child_keys:
            if key not in left_child_keys:
                if isinstance(right_comp.contents[key][0], vobject.base.Component):
                    different_components[key] = ([], right_comp.contents[key])
                else:
                    different_content_lines.append(([], right_comp.contents[key]))

        if not different_content_lines and not different_components:
            return None

        left = vobject.newFromBehavior(left_comp.name)
        right = vobject.newFromBehavior(left_comp.name)
        # add a UID, if one existed, despite the fact that they'll always be
        # the same
        uid = left_comp.getChildValue("uid")
        if uid is not None:
            left.add("uid").value = uid
            right.add("uid").value = uid

        for name, child_pair_list in different_components.items():
            left_components, right_components = zip(*child_pair_list)
            if len(left_components) > 0:
                # filter out None
                left.contents[name] = filter(None, left_components)
            if len(right_components) > 0:
                # filter out None
                right.contents[name] = filter(None, right_components)

        for left_child_line, right_child_line in different_content_lines:
            nonEmpty = left_child_line or right_child_line
            name = nonEmpty[0].name
            if left_child_line is not None:
                left.contents[name] = left_child_line
            if right_child_line is not None:
                right.contents[name] = right_child_line

        return left, right

    vevents = process_component_lists(
        sort_by_uid(getattr(left, "vevent_list", [])), sort_by_uid(getattr(right, "vevent_list", []))
    )

    vtodos = process_component_lists(
        sort_by_uid(getattr(left, "vtodo_list", [])), sort_by_uid(getattr(right, "vtodo_list", []))
    )

    return vevents + vtodos


def pretty_diff(left_obj, right_obj):
    for left, right in diff(left_obj, right_obj):
        print("<<<<<<<<<<<<<<<")
        if left is not None:
            left.prettyPrint()
        print("===============")
        if right is not None:
            right.prettyPrint()
        print(">>>>>>>>>>>>>>>")


def main():
    args = get_arguments()
    with open(args.ics_file1) as f, open(args.ics_file2) as g:
        cal1 = vobject.readOne(f)
        cal2 = vobject.readOne(g)
    delete_extraneous(cal1, ignore_dtstamp=args.ignore)
    delete_extraneous(cal2, ignore_dtstamp=args.ignore)
    pretty_diff(cal1, cal2)


def get_arguments():
    # Configuration options #
    parser = ArgumentParser(description="ics_diff will print a comparison of two iCalendar files")
    parser.add_argument("-V", "--version", action="version", version=vobject.VERSION)
    parser.add_argument(
        "-i",
        "--ignore-dtstamp",
        dest="ignore",
        action="store_true",
        default=False,
        help="ignore DTSTAMP lines [default: False]",
    )
    parser.add_argument("ics_file1", help="The first ics file to compare")
    parser.add_argument("ics_file2", help="The second ics file to compare")

    return parser.parse_args()


@deprecated
def getSortKey(component):
    return get_sort_key(component)


@deprecated
def sortByUID(components):
    return sort_by_uid(components)


@deprecated
def deleteExtraneous(component, ignore_dtstamp=False):
    return delete_extraneous(component, ignore_dtstamp)


@deprecated
def prettyDiff(leftObj, rightObj):
    return pretty_diff(leftObj, rightObj)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Aborted")
