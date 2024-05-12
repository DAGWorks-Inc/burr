import pytest

from burr.core.serde import StringDispatch, deserialize, serialize


def test_serialize_primitive_types():
    assert serialize(1) == 1
    assert serialize(1.0) == 1.0
    assert serialize("test") == "test"
    assert serialize(True) is True


def test_serialize_list():
    assert serialize([1, 2, 3]) == [1, 2, 3]
    assert serialize(["a", "b", "c"]) == ["a", "b", "c"]


def test_serialize_dict():
    assert serialize({"key": "value"}) == {"key": "value"}
    assert serialize({"key1": 1, "key2": 2}) == {"key1": 1, "key2": 2}


def test_deserialize_primitive_types():
    assert deserialize(1) == 1
    assert deserialize(1.0) == 1.0
    assert deserialize("test") == "test"
    assert deserialize(True) is True


def test_deserialize_list():
    assert deserialize([1, 2, 3]) == [1, 2, 3]
    assert deserialize(["a", "b", "c"]) == ["a", "b", "c"]


def test_deserialize_dict():
    assert deserialize({"key": "value"}) == {"key": "value"}
    assert deserialize({"key1": 1, "key2": 2}) == {"key1": 1, "key2": 2}


def test_string_dispatch_no_key():
    dispatch = StringDispatch()
    with pytest.raises(ValueError):
        dispatch.call("nonexistent_key")


def test_string_dispatch_with_key():
    dispatch = StringDispatch()
    dispatch.register("test_key")(lambda x: x)
    assert dispatch.call("test_key", "test_value") == "test_value"
