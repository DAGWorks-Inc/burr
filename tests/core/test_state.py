import pytest

from burr.core.state import SQLLitePersistence, State


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


@pytest.fixture
def persistence():
    return SQLLitePersistence(db_path=":memory:", table_name="test_table")


def test_persistence_initialization_creates_table(persistence):
    persistence.initialize()
    assert persistence.list_app_ids("partition_key") == []


def test_persistence_saves_and_loads_state(persistence):
    persistence.initialize()
    persistence.save("partition_key", "app_id", 1, "position", State({"key": "value"}), "status")
    loaded_state = persistence.load("partition_key", "app_id")
    assert loaded_state["state"] == State({"key": "value"})


def test_persistence_returns_none_when_no_state(persistence):
    persistence.initialize()
    loaded_state = persistence.load("partition_key", "app_id")
    assert loaded_state is None


def test_persistence_lists_app_ids(persistence):
    persistence.initialize()
    persistence.save("partition_key", "app_id1", 1, "position", State({"key": "value"}), "status")
    persistence.save("partition_key", "app_id2", 1, "position", State({"key": "value"}), "status")
    app_ids = persistence.list_app_ids("partition_key")
    assert set(app_ids) == set(["app_id1", "app_id2"])
