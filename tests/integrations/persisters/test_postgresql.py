import os

import pytest

from burr.core import state
from burr.integrations.persisters.postgresql import PostgreSQLPersister

if not os.environ.get("BURR_CI_INTEGRATION_TESTS") == "true":
    pytest.skip("Skipping integration tests", allow_module_level=True)


@pytest.fixture
def postgresql_persister():
    persister = PostgreSQLPersister.from_values(
        db_name="postgres",
        user="postgres",
        password="postgres",
        host="localhost",
        port=5432,
        table_name="testtable",
    )
    yield persister
    persister.connection.close()


def test_save_and_load_state(postgresql_persister):
    postgresql_persister.save("pk", "app_id", 1, "pos", state.State({"a": 1, "b": 2}), "completed")
    data = postgresql_persister.load("pk", "app_id", 1)
    assert data["state"].get_all() == {"a": 1, "b": 2}


def test_list_app_ids(postgresql_persister):
    postgresql_persister.save("pk", "app_id1", 1, "pos1", state.State({"a": 1}), "completed")
    postgresql_persister.save("pk", "app_id2", 2, "pos2", state.State({"b": 2}), "completed")
    app_ids = postgresql_persister.list_app_ids("pk")
    assert "app_id1" in app_ids
    assert "app_id2" in app_ids


def test_load_nonexistent_key(postgresql_persister):
    state_data = postgresql_persister.load("pk", "nonexistent_key")
    assert state_data is None
