"""Definitions and behavior for vCard 3.0"""

from __future__ import annotations

import codecs

from . import behavior
from .base import ContentLine, register_behavior
from .helper import backslash_escape
from .icalendar import stringToTextValues

wacky_apple_photo_serialize = True
REALLY_LARGE = 1e50
NAME_ORDER = ("family", "given", "additional", "prefix", "suffix")
ADDRESS_ORDER = ("box", "extended", "street", "city", "region", "code", "country")


# ------------------------ vCard structs ---------------------------------------
class Name:
    def __init__(self, family="", given="", additional="", prefix="", suffix=""):
        """
        Each name attribute can be a string or a list of strings.
        """
        self.family = family
        self.given = given
        self.additional = additional
        self.prefix = prefix
        self.suffix = suffix

    @staticmethod
    def toString(val):
        """
        Turn a string or array value into a string.
        """
        return " ".join(val) if type(val) in (list, tuple) else val

    def __str__(self):
        eng_order = ("prefix", "given", "additional", "family", "suffix")
        return " ".join(self.toString(getattr(self, val)) for val in eng_order)

    def __repr__(self):
        return f"<Name: {str(self)}>"

    def __eq__(self, other):
        return (
            self.family == other.family
            and self.given == other.given
            and self.additional == other.additional
            and self.prefix == other.prefix
            and self.suffix == other.suffix
        )


class Address:
    def __init__(self, street="", city="", region="", code="", country="", box="", extended=""):
        """
        Each name attribute can be a string or a list of strings.
        """
        self.box = box
        self.extended = extended
        self.street = street
        self.city = city
        self.region = region
        self.code = code
        self.country = country

    @staticmethod
    def toString(val, join_char="\n"):
        """
        Turn a string or array value into a string.
        """
        return join_char.join(val) if type(val) in (list, tuple) else val

    lines = ("box", "extended", "street")
    one_line = ("city", "region", "code")

    def __str__(self):
        lines = "\n".join(self.toString(getattr(self, val)) for val in self.lines if getattr(self, val))
        one_line = tuple(self.toString(getattr(self, val), " ") for val in self.one_line)
        lines += "\n{0!s}, {1!s} {2!s}".format(*one_line)
        if self.country:
            lines += "\n" + self.toString(self.country)
        return lines

    def __repr__(self):
        return "<Address: {0!s}>".format(self)

    def __eq__(self, other):
        try:
            return (
                self.box == other.box
                and self.extended == other.extended
                and self.street == other.street
                and self.city == other.city
                and self.region == other.region
                and self.code == other.code
                and self.country == other.country
            )
        except AttributeError:
            return False


# ------------------------ Registered Behavior subclasses ----------------------


class VCardTextBehavior(behavior.Behavior):
    """
    Provide backslash escape encoding/decoding for single valued properties.

    TextBehavior also deals with base64 encoding if the ENCODING parameter is
    explicitly set to BASE64.
    """

    allowGroup = True
    base64string = "B"

    @classmethod
    def decode(cls, line):
        """
        Remove backslash escaping from line.valueDecode line, either to remove
        backslash escaping, or to decode base64 encoding. The content line should
        contain a ENCODING=b for base64 encoding, but Apple Addressbook seems to
        export a singleton parameter of 'BASE64', which does not match the 3.0
        vCard spec. If we encounter that, then we transform the parameter to
        ENCODING=b
        """
        if line.encoded:
            if "BASE64" in line.singletonparams:
                line.singletonparams.remove("BASE64")
                line.encoding_param = cls.base64string
            encoding = getattr(line, "encoding_param", None)
            if encoding:
                if not isinstance(line.value, bytes):
                    line.value = line.value.encode("utf-8")
                line.value = codecs.decode(line.value, "base64")
            else:
                line.value = stringToTextValues(line.value)[0]
            line.encoded = False

    @classmethod
    def encode(cls, line):
        """
        Backslash escape line.value.
        """
        if not line.encoded:
            encoding = getattr(line, "encoding_param", None)
            if encoding and encoding.upper() == cls.base64string:
                if isinstance(line.value, bytes):
                    line.value = codecs.encode(line.value, "base64").decode("utf-8").replace("\n", "")
                else:
                    line.value = codecs.encode(line.value.encode(encoding), "base64").decode("utf-8")
            else:
                line.value = backslash_escape(line.value)
            line.encoded = True


class VCardBehavior(behavior.Behavior):
    allowGroup = True
    defaultBehavior = VCardTextBehavior


class VCard3(VCardBehavior):
    """
    vCard 3.0 behavior.
    """

    name = "VCARD"
    description = "vCard 3.0, defined in rfc2426"
    versionString = "3.0"
    isComponent = True
    sortFirst = ("version", "prodid", "uid")
    knownChildren = {
        "N": (0, 1, None),  # min, max, behaviorRegistry id
        "FN": (1, None, None),
        "VERSION": (1, 1, None),  # required, auto-generated
        "PRODID": (0, 1, None),
        "LABEL": (0, None, None),
        "UID": (0, None, None),
        "ADR": (0, None, None),
        "ORG": (0, None, None),
        "PHOTO": (0, None, None),
        "CATEGORIES": (0, None, None),
    }

    @classmethod
    def generateImplicitParameters(cls, obj):
        """
        Create PRODID, VERSION, and VTIMEZONEs if needed.

        VTIMEZONEs will need to exist whenever TZID parameters exist or when
        datetimes with tzinfo exist.
        """
        if not hasattr(obj, "version"):
            obj.add(ContentLine("VERSION", [], cls.versionString))


register_behavior(VCard3, default=True)


class FN(VCardTextBehavior):
    name = "FN"
    description = "Formatted name"


register_behavior(FN)


class Label(VCardTextBehavior):
    name = "Label"
    description = "Formatted address"


register_behavior(Label)


class Photo(VCardTextBehavior):
    name = "Photo"
    description = "Photograph"

    @classmethod
    def valueRepr(cls, line):
        return f" (BINARY PHOTO DATA at 0x{id(line.value)!s}) "

    @classmethod
    def serialize(cls, obj, buf, line_length, validate=True, *args, **kwargs):
        """
        Apple's Address Book is *really* weird with images, it expects
        base64 data to have very specific whitespace.  It seems Address Book
        can handle PHOTO if it's not wrapped, so don't wrap it.
        """
        if wacky_apple_photo_serialize:
            line_length = REALLY_LARGE
        VCardTextBehavior.serialize(obj, buf, line_length, validate, *args, **kwargs)


register_behavior(Photo)


def toListOrString(string):
    stringList = stringToTextValues(string)
    return stringList[0] if len(stringList) == 1 else stringList


def splitFields(string):
    """
    Return a list of strings or lists from a Name or Address.
    """
    return [toListOrString(i) for i in stringToTextValues(string, listSeparator=";", charList=";")]


def toList(string_or_list) -> list[str]:
    return [string_or_list] if isinstance(string_or_list, str) else string_or_list


def serializeFields(obj, order=None):
    """
    Turn an object's fields into a ';' and ',' separated string.

    If order is None, obj should be a list, backslash escape each field and
    return a ';' separated string.
    """
    fields = []
    if order is None:
        fields = [backslash_escape(val) for val in obj]
    else:
        for field in order:
            escapedValueList = [backslash_escape(val) for val in toList(getattr(obj, field))]
            fields.append(",".join(escapedValueList))
    return ";".join(fields)


class NameBehavior(VCardBehavior):
    """
    A structured name.
    """

    hasNative = True

    @staticmethod
    def transformToNative(obj):
        """
        Turn obj.value into a Name.
        """
        if obj.isNative:
            return obj
        obj.isNative = True
        obj.value = Name(**dict(zip(NAME_ORDER, splitFields(obj.value))))
        return obj

    @staticmethod
    def transformFromNative(obj):
        """
        Replace the Name in obj.value with a string.
        """
        obj.isNative = False
        obj.value = serializeFields(obj.value, NAME_ORDER)
        return obj


register_behavior(NameBehavior, "N")


class AddressBehavior(VCardBehavior):
    """
    A structured address.
    """

    hasNative = True

    @staticmethod
    def transformToNative(obj):
        """
        Turn obj.value into an Address.
        """
        if obj.isNative:
            return obj
        obj.isNative = True
        obj.value = Address(**dict(zip(ADDRESS_ORDER, splitFields(obj.value))))
        return obj

    @staticmethod
    def transformFromNative(obj):
        """
        Replace the Address in obj.value with a string.
        """
        obj.isNative = False
        obj.value = serializeFields(obj.value, ADDRESS_ORDER)
        return obj


register_behavior(AddressBehavior, "ADR")


class OrgBehavior(VCardBehavior):
    """
    A list of organization values and sub-organization values.
    """

    hasNative = True

    @staticmethod
    def transformToNative(obj):
        """
        Turn obj.value into a list.
        """
        if obj.isNative:
            return obj
        obj.isNative = True
        obj.value = splitFields(obj.value)
        return obj

    @staticmethod
    def transformFromNative(obj):
        """
        Replace the list in obj.value with a string.
        """
        if not obj.isNative:
            return obj
        obj.isNative = False
        obj.value = serializeFields(obj.value)
        return obj


register_behavior(OrgBehavior, "ORG")
