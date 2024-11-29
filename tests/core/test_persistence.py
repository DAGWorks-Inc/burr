import pytest

from burr.core import State
from burr.core.persistence import InMemoryPersister, SQLLitePersister


@pytest.fixture(
    params=[
        {"which": "sqlite"},
        {"which": "memory"},
    ]
)
def persistence(request):
    which = request.param["which"]
    if which == "sqlite":
        return SQLLitePersister(db_path=":memory:", table_name="test_table")
    elif which == "memory":
        return InMemoryPersister()
    # return SQLLitePersister(db_path=":memory:", table_name="test_table")


@pytest.fixture()
def initializing_persistence():
    return SQLLitePersister(db_path=":memory:", table_name="test_table")


def test_persistence_initialization_creates_table(initializing_persistence):
    initializing_persistence.initialize()
    assert initializing_persistence.list_app_ids("partition_key") == []


def test_persistence_saves_and_loads_state(persistence):
    if hasattr(persistence, "initialize"):
        persistence.initialize()
    persistence.save("partition_key", "app_id", 1, "position", State({"key": "value"}), "status")
    loaded_state = persistence.load("partition_key", "app_id")
    assert loaded_state["state"] == State({"key": "value"})


def test_persistence_returns_none_when_no_state(persistence):
    if hasattr(persistence, "initialize"):
        persistence.initialize()
    loaded_state = persistence.load("partition_key", "app_id")
    assert loaded_state is None


def test_persistence_lists_app_ids(persistence):
    if hasattr(persistence, "initialize"):
        persistence.initialize()
    persistence.save("partition_key", "app_id1", 1, "position", State({"key": "value"}), "status")
    persistence.save("partition_key", "app_id2", 1, "position", State({"key": "value"}), "status")
    app_ids = persistence.list_app_ids("partition_key")
    assert set(app_ids) == set(["app_id1", "app_id2"])


def test_persistence_is_initialized_false(initializing_persistence):
    assert not initializing_persistence.is_initialized()


def test_persistence_is_initialized_true(initializing_persistence):
    initializing_persistence.initialize()
    assert initializing_persistence.is_initialized()


def test_sqlite_persistence_is_initialized_true_new_connection(tmp_path):
    db_path = tmp_path / "test.db"
    p = SQLLitePersister(db_path=db_path, table_name="test_table")
    p.initialize()
    assert p.is_initialized()
    p2 = SQLLitePersister(db_path=db_path, table_name="test_table")
    assert p2.is_initialized()


@pytest.mark.parametrize(
    "method_name,kwargs",
    [
        ("list_app_ids", {"partition_key": None}),
        ("load", {"partition_key": None, "app_id": "foo"}),
        (
            "save",
            {
                "partition_key": None,
                "app_id": "foo",
                "sequence_id": 1,
                "position": "position",
                "state": State({"key": "value"}),
                "status": "status",
            },
        ),
    ],
)
def test_persister_methods_none_partition_key(persistence, method_name: str, kwargs: dict):
    if hasattr(persistence, "initialize"):
        persistence.initialize()
    method = getattr(persistence, method_name)
    # method can be executed with `partition_key=None`
    method(**kwargs)
    # this doesn't guarantee that the results of `partition_key=None` and
    # `partition_key=persistence.PARTITION_KEY_DEFAULT`. This is hard to test because
    # these operations are stateful (i.e., read/write to a db)
