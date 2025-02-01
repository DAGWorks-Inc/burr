import os
import pickle

import pytest

from burr.core import state
from burr.integrations.persisters.b_asyncpg import AsyncPostgreSQLPersister
from burr.integrations.persisters.b_psycopg2 import PostgreSQLPersister

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
    persister.initialize()
    yield persister
    persister.cleanup()


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


def test_is_initialized(postgresql_persister):
    """Tests that a new connection also returns True for is_initialized."""
    assert postgresql_persister.is_initialized()
    persister2 = PostgreSQLPersister.from_values(
        db_name="postgres",
        user="postgres",
        password="postgres",
        host="localhost",
        port=5432,
        table_name="testtable",
    )
    assert persister2.is_initialized()


def test_is_initialized_false():
    persister = PostgreSQLPersister.from_values(
        db_name="postgres",
        user="postgres",
        password="postgres",
        host="localhost",
        port=5432,
        table_name="testtable2",
    )
    assert not persister.is_initialized()


def test_serialization_with_pickle(postgresql_persister):
    # Save some state
    postgresql_persister.save(
        "pk", "app_id_serde", 1, "pos", state.State({"a": 1, "b": 2}), "completed"
    )

    # Serialize the persister
    serialized_persister = pickle.dumps(postgresql_persister)

    # Deserialize the persister
    deserialized_persister = pickle.loads(serialized_persister)

    # Load the state from the deserialized persister
    data = deserialized_persister.load("pk", "app_id_serde", 1)

    assert data["state"].get_all() == {"a": 1, "b": 2}


@pytest.fixture
async def asyncpostgresql_persister():
    persister = await AsyncPostgreSQLPersister.from_values(
        db_name="postgres",
        user="postgres",
        password="postgres",
        host="localhost",
        port=5432,
        table_name="testtable_async",
    )
    await persister.initialize()
    yield persister
    await persister.cleanup()


async def test_async_pg_fixture(asyncpostgresql_persister):
    assert await asyncpostgresql_persister.is_initialized()


async def test_async_is_initialized_false():
    persister = await AsyncPostgreSQLPersister.from_values(
        db_name="postgres",
        user="postgres",
        password="postgres",
        host="localhost",
        port=5432,
        table_name="testtable_async2",
    )
    assert not await persister.is_initialized()


async def test_async_save_and_load_state(asyncpostgresql_persister):
    await asyncpostgresql_persister.save(
        "pk", "app_id", 1, "pos", state.State({"a": 1, "b": 2}), "completed"
    )
    data = await asyncpostgresql_persister.load("pk", "app_id", 1)
    print(data)
    assert data["state"].get_all() == {"a": 1, "b": 2}


async def test_async_list_app_ids(asyncpostgresql_persister):
    await asyncpostgresql_persister.save(
        "pk", "app_id1", 1, "pos1", state.State({"a": 1}), "completed"
    )
    await asyncpostgresql_persister.save(
        "pk", "app_id2", 2, "pos2", state.State({"b": 2}), "completed"
    )
    app_ids = await asyncpostgresql_persister.list_app_ids("pk")
    assert "app_id1" in app_ids
    assert "app_id2" in app_ids


async def test_async_load_nonexistent_key(asyncpostgresql_persister):
    state_data = await asyncpostgresql_persister.load("pk", "nonexistent_key")
    assert state_data is None
