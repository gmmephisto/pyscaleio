from __future__ import unicode_literals

from collections import MutableMapping, MutableSequence
from functools import wraps


def _drop_none(mapping):
    """
    Removes all keys that points to None values.

    >>> _drop_none({})
    {}
    >>> _drop_none({'a': 'A', 'b': 'B'}) == {'a': 'A', 'b': 'B'}
    True
    >>> _drop_none({'a': 'A', 'b': None}) == {'a': 'A'}
    True
    >>> _drop_none({'a': 'A', 'b': None, 'c': 'C', 'd': None}) == {'a': 'A', 'c': 'C'}
    True
    >>> _drop_none(('a', 'b'))
    Traceback (most recent call last):
    ...
    AssertionError: assert isinstance(('a', 'b'), MutableMapping)
    """

    assert isinstance(mapping, MutableMapping)
    for key in mapping.copy():
        if mapping[key] is None:
            mapping.pop(key)

    return mapping


def drop_none(func):
    """
    >>> drop_none(lambda: {'a': 'A', 'b': None})() == {'a': 'A'}
    True
    >>> drop_none(lambda: [{'a': 'A', 'b': None}])() == [{'a': 'A'}]
    True
    >>> drop_none(lambda: "test")() == "test"
    True
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        results = func(*args, **kwargs)
        if isinstance(results, MutableSequence):
            return [_drop_none(result) for result in results]
        elif isinstance(results, MutableMapping):
            return _drop_none(func(*args, **kwargs))
        else:
            return results
    return wrapper


def bool_to_str(value):
    """
    Converts bool value to string.

    >>> bool_to_str(True) == "TRUE"
    True
    >>> bool_to_str(False) == "FALSE"
    True
    >>> bool_to_str("test")
    Traceback (most recent call last):
    ...
    AssertionError: assert isinstance('test', bool)
    """

    assert isinstance(value, bool)

    return "TRUE" if value is True else "FALSE"
