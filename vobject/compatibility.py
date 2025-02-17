import warnings
from functools import wraps


def deprecated(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        warnings.warn(f"{func.__name__} is deprecated, use snake_case instead", DeprecationWarning)
        return func(*args, **kwargs)

    return wrapper
