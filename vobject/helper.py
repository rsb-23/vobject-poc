# ------------------------------------ Logging ---------------------------------
import functools
import logging
import re
import warnings
from typing import Generator

logger = logging.getLogger(__name__)
if not logging.getLogger().handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(name)s:%(lineno)d %(levelname)s %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)  # modify log levels here

# ----------------------------------- Constants --------------------------------
CR = "\r"
LF = "\n"
CRLF = CR + LF
SPACE = " "
TAB = "\t"
SPACEORTAB = SPACE + TAB


# -----Decorators-----


def deprecated(func=None):
    """This is a decorator which can be used to mark functions as deprecated.
    It will result in a warning being emitted when the function is used."""

    def camel_to_snake(name):
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        x = re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()
        return x.replace("date_time", "datetime")

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


def test_case(func):
    """This is a decorator logs inputs and outputs of a func"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.warning(func.__name__)
        logger.warning(f"{args=}, {kwargs}")
        result = func(*args, **kwargs)
        logger.warning(f"{result=}")
        return result

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


def split_by_size(text: str, byte_size: int) -> Generator:
    start = space_count = 0
    encoded = text.encode()
    total_size = len(encoded)
    while start < total_size - byte_size:
        k = byte_size - space_count + start
        while (encoded[k] & 0xC0) == 0x80:
            k -= 1
        yield encoded[start:k].decode() + "\r\n "
        space_count = 1
        start = k
    yield encoded[start:].decode()
