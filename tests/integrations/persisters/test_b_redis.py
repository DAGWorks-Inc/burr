import os

import pytest

from burr.core import state
from burr.integrations.persisters.b_redis import RedisPersister

if not os.environ.get("BURR_CI_INTEGRATION_TESTS") == "true":
    pytest.skip("Skipping integration tests", allow_module_level=True)


@pytest.fixture
def redis_persister():
    persister = RedisPersister(host="localhost", port=6379, db=0)
    yield persister
    persister.connection.close()


@pytest.fixture
def redis_persister_with_ns():
    persister = RedisPersister(host="localhost", port=6379, db=0, namespace="test")
    yield persister
    persister.connection.close()


def test_save_and_load_state(redis_persister):
    redis_persister.save("pk", "app_id", 1, "pos", state.State({"a": 1, "b": 2}), "completed")
    data = redis_persister.load("pk", "app_id", 1)
    assert data["state"].get_all() == {"a": 1, "b": 2}


def test_list_app_ids(redis_persister):
    redis_persister.save("pk", "app_id1", 1, "pos1", state.State({"a": 1}), "completed")
    redis_persister.save("pk", "app_id2", 2, "pos2", state.State({"b": 2}), "completed")
    app_ids = redis_persister.list_app_ids("pk")
    assert "app_id1" in app_ids
    assert "app_id2" in app_ids


def test_load_nonexistent_key(redis_persister):
    state_data = redis_persister.load("pk", "nonexistent_key")
    assert state_data is None


def test_save_and_load_state_ns(redis_persister_with_ns):
    redis_persister_with_ns.save(
        "pk", "app_id", 1, "pos", state.State({"a": 1, "b": 2}), "completed"
    )
    data = redis_persister_with_ns.load("pk", "app_id", 1)
    assert data["state"].get_all() == {"a": 1, "b": 2}


def test_list_app_ids_with_ns(redis_persister_with_ns):
    redis_persister_with_ns.save("pk", "app_id1", 1, "pos1", state.State({"a": 1}), "completed")
    redis_persister_with_ns.save("pk", "app_id2", 2, "pos2", state.State({"b": 2}), "completed")
    app_ids = redis_persister_with_ns.list_app_ids("pk")
    assert "app_id1" in app_ids
    assert "app_id2" in app_ids


def test_load_nonexistent_key_with_ns(redis_persister_with_ns):
    state_data = redis_persister_with_ns.load("pk", "nonexistent_key")
    assert state_data is None
