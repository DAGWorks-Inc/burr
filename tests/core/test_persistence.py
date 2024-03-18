import pytest

from burr.core import State
from burr.core.persistence import SQLLitePersister


@pytest.fixture
def persistence():
    return SQLLitePersister(db_path=":memory:", table_name="test_table")


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
