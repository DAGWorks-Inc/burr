import pytest

from burr.core.state import State, register_field_serde


def test_state_access():
    state = State({"foo": "bar"})
    assert state["foo"] == "bar"


def test_state_access_missing():
    state = State({"foo": "bar"})
    with pytest.raises(KeyError):
        _ = state["baz"]


def test_state_get():
    state = State({"foo": "bar"})
    assert state.get("foo") == "bar"


def test_state_get_missing():
    state = State({"foo": "bar"})
    assert state.get("baz") is None


def test_state_get_missing_default():
    state = State({"foo": "bar"})
    assert state.get("baz", "qux") == "qux"


def test_state_in():
    state = State({"foo": "bar"})
    assert "foo" in state
    assert "baz" not in state


def test_state_get_all():
    state = State({"foo": "bar", "baz": "qux"})
    assert state.get_all() == {"foo": "bar", "baz": "qux"}


def test_state_merge():
    state = State({"foo": "bar", "baz": "qux"})
    other = State({"foo": "baz", "quux": "corge"})
    merged = state.merge(other)
    assert merged.get_all() == {"foo": "baz", "baz": "qux", "quux": "corge"}


def test_state_subset():
    state = State({"foo": "bar", "baz": "qux"})
    subset = state.subset("foo")
    assert subset.get_all() == {"foo": "bar"}


def test_state_append():
    state = State({"foo": ["bar"]})
    appended = state.append(foo="baz")
    assert appended.get_all() == {"foo": ["bar", "baz"]}


def test_state_update():
    state = State({"foo": "bar", "baz": "qux"})
    updated = state.update(foo="baz")
    assert updated.get_all() == {"foo": "baz", "baz": "qux"}


def test_state_init():
    state = State({"foo": "bar", "baz": "qux"})
    assert state.get_all() == {"foo": "bar", "baz": "qux"}


def test_state_wipe_delete():
    state = State({"foo": "bar", "baz": "qux"})
    wiped = state.wipe(delete=["foo"])
    assert wiped.get_all() == {"baz": "qux"}


def test_state_wipe_keep():
    state = State({"foo": "bar", "baz": "qux"})
    wiped = state.wipe(keep=["foo"])
    assert wiped.get_all() == {"foo": "bar"}


def test_state_append_validate_failure():
    state = State({"foo": "bar"})
    with pytest.raises(ValueError, match="non-appendable"):
        state.append(foo="baz", bar="qux")


def test_state_increment():
    state = State({"foo": 1})
    incremented = state.increment(foo=2, bar=5)
    assert incremented.get_all() == {"foo": 3, "bar": 5}


def test_state_increment_validate_failure():
    state = State({"foo": "bar"})
    with pytest.raises(ValueError, match="non-integer"):
        state.increment(foo="baz", bar="qux")


def test_field_level_serde():
    def my_field_serializer(value: str, **kwargs) -> dict:
        serde_value = f"serialized_{value}"
        return {"value": serde_value}

    def my_field_deserializer(value: dict, **kwargs) -> str:
        serde_value = value["value"]
        return serde_value.replace("serialized_", "")

    register_field_serde("my_field", my_field_serializer, my_field_deserializer)
    state = State({"foo": {"hi": "world"}, "baz": "qux", "my_field": "testing 123"})
    assert state.serialize() == {
        "foo": {"hi": "world"},
        "baz": "qux",
        "my_field": {"value": "serialized_testing 123"},
    }
    state = State.deserialize(
        {"foo": {"hi": "world"}, "baz": "qux", "my_field": {"value": "serialized_testing 123"}}
    )
    assert state.get_all() == {"foo": {"hi": "world"}, "baz": "qux", "my_field": "testing 123"}


def test_field_level_serde_bad_serde_function():
    def my_field_serializer(value: str, **kwargs) -> str:
        # bad function
        serde_value = f"serialized_{value}"
        return serde_value

    def my_field_deserializer(value: dict, **kwargs) -> str:
        serde_value = value["value"]
        return serde_value.replace("serialized_", "")

    register_field_serde("my_field", my_field_serializer, my_field_deserializer)
    state = State({"foo": {"hi": "world"}, "baz": "qux", "my_field": "testing 123"})
    with pytest.raises(ValueError):
        state.serialize()


def test_register_field_serde_check_no_kwargs():
    def my_field_serializer(value: str) -> dict:
        serde_value = f"serialized_{value}"
        return {"value": serde_value}

    def my_field_deserializer(value: dict) -> str:
        serde_value = value["value"]
        return serde_value.replace("serialized_", "")

    with pytest.raises(ValueError):
        # serializer & deserializer missing kwargs
        register_field_serde("my_field", my_field_serializer, my_field_deserializer)

    def my_field_serializer(value: str, **kwargs) -> dict:
        serde_value = f"serialized_{value}"
        return {"value": serde_value}

    with pytest.raises(ValueError):
        # deserializer still bad
        register_field_serde("my_field", my_field_serializer, my_field_deserializer)
