# ------------------------------------ Logging ---------------------------------
import functools
import logging
import re
import warnings

logger = logging.getLogger(__name__)
if not logging.getLogger().handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(name)s %(levelname)s %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.ERROR)  # Log errors
DEBUG = False  # Don't waste time on debug calls

# ----------------------------------- Constants --------------------------------
CR = "\r"
LF = "\n"
CRLF = CR + LF
SPACE = " "
TAB = "\t"
SPACEORTAB = SPACE + TAB


# -----Deprecation decorator-----


def deprecated(func=None):
    """This is a decorator which can be used to mark functions as deprecated.
    It will result in a warning being emitted when the function is used."""

    def camel_to_snake(name):
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        func_name = func.__name__
        warnings.simplefilter("always", DeprecationWarning)  # turn off filter
        new_func = camel_to_snake(func_name)
        warnings.warn(
            f"{func_name}() is deprecated, use {new_func}() instead", category=DeprecationWarning, stacklevel=2
        )
        warnings.simplefilter("default", DeprecationWarning)  # reset filter
        return func(*args, **kwargs)

    return wrapper


# --------------------------- Helper function ----------------------------------


@deprecated
def backslashEscape(s):
    return backslash_escape(s)


def backslash_escape(s):
    s = s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,")
    return s.replace("\r\n", "\\n").replace("\n", "\\n").replace("\r", "\\n")


def indent_str(prefix: str = " ", *, level: int = 0, tabwidth: int = 3) -> str:
    return prefix * level * tabwidth
