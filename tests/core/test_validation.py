import pytest

from burr.core.validation import assert_set


def test__assert_set():
    assert_set("foo", "foo", "bar")


def test__assert_set_unset():
    with pytest.raises(ValueError, match="bar"):
        assert_set(None, "foo", "bar")
