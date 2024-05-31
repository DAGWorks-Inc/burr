import os

import pytest

from burr.core import state
from burr.integrations.persisters.b_mongodb import MongoDBPersister

if not os.environ.get("BURR_CI_INTEGRATION_TESTS") == "true":
    pytest.skip("Skipping integration tests", allow_module_level=True)


@pytest.fixture
def mongodb_persister():
    persister = MongoDBPersister(
        uri="mongodb://localhost:27017", db_name="testdb", collection_name="testcollection"
    )
    yield persister
    persister.collection.drop()


def test_save_and_load_state(mongodb_persister):
    mongodb_persister.save("pk", "app_id", 1, "pos", state.State({"a": 1, "b": 2}), "completed")
    data = mongodb_persister.load("pk", "app_id", 1)
    assert data["state"].get_all() == {"a": 1, "b": 2}


def test_list_app_ids(mongodb_persister):
    mongodb_persister.save("pk", "app_id1", 1, "pos1", state.State({"a": 1}), "completed")
    mongodb_persister.save("pk", "app_id2", 2, "pos2", state.State({"b": 2}), "completed")
    app_ids = mongodb_persister.list_app_ids("pk")
    assert "app_id1" in app_ids
    assert "app_id2" in app_ids


def test_load_nonexistent_key(mongodb_persister):
    state_data = mongodb_persister.load("pk", "nonexistent_key")
    assert state_data is None
