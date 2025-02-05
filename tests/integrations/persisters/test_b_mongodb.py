import os
import pickle

import pytest

from burr.core import state
from burr.integrations.persisters.b_mongodb import MongoDBPersister
from burr.integrations.persisters.b_pymongo import MongoDBBasePersister

if not os.environ.get("BURR_CI_INTEGRATION_TESTS") == "true":
    pytest.skip("Skipping integration tests", allow_module_level=True)


@pytest.fixture
def mongodb_persister():
    persister = MongoDBBasePersister.from_values(
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


def test_backwards_compatible_persister():
    persister = MongoDBPersister(
        uri="mongodb://localhost:27017", db_name="testdb", collection_name="backwardscompatible"
    )
    persister.save("pk", "app_id", 5, "pos", state.State({"a": 5, "b": 5}), "completed")
    data = persister.load("pk", "app_id", 5)
    assert data["state"].get_all() == {"a": 5, "b": 5}

    persister.collection.drop()


def test_serialization_with_pickle(mongodb_persister):
    # Save some state
    mongodb_persister.save(
        "pk", "app_id_serde", 1, "pos", state.State({"a": 1, "b": 2}), "completed"
    )

    # Serialize the persister
    serialized_persister = pickle.dumps(mongodb_persister)

    # Deserialize the persister
    deserialized_persister = pickle.loads(serialized_persister)

    # Load the state from the deserialized persister
    data = deserialized_persister.load("pk", "app_id_serde", 1)

    assert data["state"].get_all() == {"a": 1, "b": 2}


def test_partition_key_is_optional(mongodb_persister):
    # 1. Save and load with partition key = None
    mongodb_persister.save(
        None, "app_id_none", 1, "pos1", state.State({"foo": "bar"}), "in_progress"
    )
    loaded_data = mongodb_persister.load(None, "app_id_none", 1)
    assert loaded_data is not None
    assert loaded_data["state"].get_all() == {"foo": "bar"}

    # 2. Save and load again (different key/index) with partition key = None
    mongodb_persister.save(
        None, "app_id_none2", 2, "pos2", state.State({"hello": "world"}), "completed"
    )
    loaded_data2 = mongodb_persister.load(None, "app_id_none2", 2)
    assert loaded_data2 is not None
    assert loaded_data2["state"].get_all() == {"hello": "world"}
