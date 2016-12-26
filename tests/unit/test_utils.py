from __future__ import unicode_literals

import pytest

from pyscaleio import utils


@pytest.mark.parametrize(("inputs", "result"), [
    ({}, {}),
    ({'a': 'A', 'b': 'B'}, {'a': 'A', 'b': 'B'}),
    ({'a': 'A', 'b': None}, {'a': 'A'}),
    ({'a': 'A', 'b': None, 'c': 'C', 'd': None}, {'a': 'A', 'c': 'C'}),
    (('a', 'b'), AssertionError()),
])
def test__drop_none(inputs, result):

    if isinstance(result, Exception):
        with pytest.raises(type(result)):
            utils._drop_none(inputs)
    else:
        assert utils._drop_none(inputs) == result


@pytest.mark.parametrize(("inputs", "result"), [
    (True, "TRUE"), (False, "FALSE"), ("test", AssertionError()),
])
def test_bool_to_str(inputs, result):

    if isinstance(result, Exception):
        with pytest.raises(type(result)):
            utils.bool_to_str(inputs)
    else:
        assert utils.bool_to_str(inputs) == result
