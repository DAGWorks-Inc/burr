import asyncio
from typing import Tuple

import aiosqlite
import pytest

from burr.core import ApplicationBuilder, State, action
from burr.integrations.persisters.b_aiosqlite import AsyncSQLitePersister


class AsyncSQLiteContextManager:
    def __init__(self, sqlite_object):
        self.client = sqlite_object

    async def __aenter__(self):
        return self.client

    async def __aexit__(self, exc_type, exc, tb):
        await self.client.cleanup()


async def test_copy_persister(async_persistence: AsyncSQLitePersister):
    copy = async_persistence.copy()
    assert copy.table_name == async_persistence.table_name
    assert copy.serde_kwargs == async_persistence.serde_kwargs
    assert copy.connection is not None


@pytest.fixture()
async def async_persistence(request):
    sqlite_persister = await AsyncSQLitePersister.from_values(
        db_path=":memory:", table_name="test_table"
    )
    async_context_manager = AsyncSQLiteContextManager(sqlite_persister)
    async with async_context_manager as client:
        yield client


async def test_async_persistence_saves_and_loads_state(async_persistence):
    await asyncio.sleep(0.00001)
    if hasattr(async_persistence, "initialize"):
        await async_persistence.initialize()
    await async_persistence.save(
        "partition_key", "app_id", 1, "position", State({"key": "value"}), "status"
    )
    loaded_state = await async_persistence.load("partition_key", "app_id")
    assert loaded_state["state"] == State({"key": "value"})


async def test_async_persistence_returns_none_when_no_state(async_persistence):
    await asyncio.sleep(0.00001)
    if hasattr(async_persistence, "initialize"):
        await async_persistence.initialize()
    loaded_state = await async_persistence.load("partition_key", "app_id")
    assert loaded_state is None


async def test_async_persistence_lists_app_ids(async_persistence):
    await asyncio.sleep(0.00001)
    if hasattr(async_persistence, "initialize"):
        await async_persistence.initialize()
    await async_persistence.save(
        "partition_key", "app_id1", 1, "position", State({"key": "value"}), "status"
    )
    await async_persistence.save(
        "partition_key", "app_id2", 1, "position", State({"key": "value"}), "status"
    )
    app_ids = await async_persistence.list_app_ids("partition_key")
    assert set(app_ids) == set(["app_id1", "app_id2"])


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
async def test_async_persister_methods_none_partition_key(
    async_persistence, method_name: str, kwargs: dict
):
    await asyncio.sleep(0.00001)
    if hasattr(async_persistence, "initialize"):
        await async_persistence.initialize()
    method = getattr(async_persistence, method_name)
    # method can be executed with `partition_key=None`
    await method(**kwargs)
    # this doesn't guarantee that the results of `partition_key=None` and
    # `partition_key=persistence.PARTITION_KEY_DEFAULT`. This is hard to test because
    # these operations are stateful (i.e., read/write to a db)


async def test_AsyncSQLitePersister_from_values():
    await asyncio.sleep(0.00001)
    connection = await aiosqlite.connect(":memory:")
    sqlite_persister_init = AsyncSQLitePersister(connection=connection, table_name="test_table")
    sqlite_persister_from_values = await AsyncSQLitePersister.from_values(
        db_path=":memory:", table_name="test_table"
    )

    try:
        sqlite_persister_init.connection == sqlite_persister_from_values.connection
    except Exception as e:
        raise e
    finally:
        await sqlite_persister_init.close()
        await sqlite_persister_from_values.close()


async def test_AsyncSQLitePersister_connection_shutdown():
    await asyncio.sleep(0.00001)
    sqlite_persister = await AsyncSQLitePersister.from_values(
        db_path=":memory:", table_name="test_table"
    )
    await sqlite_persister.close()


@pytest.fixture()
async def initializing_async_persistence():
    sqlite_persister = await AsyncSQLitePersister.from_values(
        db_path=":memory:", table_name="test_table"
    )
    async_context_manager = AsyncSQLiteContextManager(sqlite_persister)
    async with async_context_manager as client:
        yield client


async def test_async_persistence_initialization_creates_table(initializing_async_persistence):
    await asyncio.sleep(0.00001)
    await initializing_async_persistence.initialize()
    assert await initializing_async_persistence.list_app_ids("partition_key") == []


async def test_async_persistence_is_initialized_false(initializing_async_persistence):
    await asyncio.sleep(0.00001)
    assert not await initializing_async_persistence.is_initialized()


async def test_async_persistence_is_initialized_true(initializing_async_persistence):
    await asyncio.sleep(0.00001)
    await initializing_async_persistence.initialize()
    assert await initializing_async_persistence.is_initialized()


async def test_asyncsqlite_persistence_is_initialized_true_new_connection(tmp_path):
    await asyncio.sleep(0.00001)
    db_path = tmp_path / "test.db"
    p = await AsyncSQLitePersister.from_values(db_path=db_path, table_name="test_table")
    await p.initialize()
    p2 = await AsyncSQLitePersister.from_values(db_path=db_path, table_name="test_table")
    try:
        assert await p.is_initialized()
        assert await p2.is_initialized()
    except Exception as e:
        raise e
    finally:
        await p.close()
        await p2.close()


async def test_async_save_and_load_from_sqlite_persister_end_to_end(tmp_path):
    await asyncio.sleep(0.00001)

    @action(reads=[], writes=["prompt", "chat_history"])
    async def dummy_input(state: State) -> Tuple[dict, State]:
        await asyncio.sleep(0.0001)
        if state["chat_history"]:
            new = state["chat_history"][-1] + 1
        else:
            new = 1
        return (
            {"prompt": "PROMPT"},
            state.update(prompt="PROMPT").append(chat_history=new),
        )

    @action(reads=["chat_history"], writes=["response", "chat_history"])
    async def dummy_response(state: State) -> Tuple[dict, State]:
        await asyncio.sleep(0.0001)
        if state["chat_history"]:
            new = state["chat_history"][-1] + 1
        else:
            new = 1
        return (
            {"response": "RESPONSE"},
            state.update(response="RESPONSE").append(chat_history=new),
        )

    db_path = tmp_path / "test.db"
    sqlite_persister = await AsyncSQLitePersister.from_values(
        db_path=db_path, table_name="test_table"
    )
    await sqlite_persister.initialize()
    app = await (
        ApplicationBuilder()
        .with_actions(dummy_input, dummy_response)
        .with_transitions(("dummy_input", "dummy_response"), ("dummy_response", "dummy_input"))
        .initialize_from(
            initializer=sqlite_persister,
            resume_at_next_action=True,
            default_state={"chat_history": []},
            default_entrypoint="dummy_input",
        )
        .with_state_persister(sqlite_persister)
        .with_identifiers(app_id="test_1", partition_key="sqlite")
        .abuild()
    )

    try:
        *_, state = await app.arun(halt_after=["dummy_response"])
        assert state["chat_history"][0] == 1
        assert state["chat_history"][1] == 2
        del app
    except Exception as e:
        raise e
    finally:
        await sqlite_persister.close()
        del sqlite_persister

    sqlite_persister_2 = await AsyncSQLitePersister.from_values(
        db_path=db_path, table_name="test_table"
    )
    await sqlite_persister_2.initialize()
    new_app = await (
        ApplicationBuilder()
        .with_actions(dummy_input, dummy_response)
        .with_transitions(("dummy_input", "dummy_response"), ("dummy_response", "dummy_input"))
        .initialize_from(
            initializer=sqlite_persister_2,
            resume_at_next_action=True,
            default_state={"chat_history": []},
            default_entrypoint="dummy_input",
        )
        .with_state_persister(sqlite_persister_2)
        .with_identifiers(app_id="test_1", partition_key="sqlite")
        .abuild()
    )

    try:
        assert new_app.state["chat_history"][0] == 1
        assert new_app.state["chat_history"][1] == 2

        *_, state = await new_app.arun(halt_after=["dummy_response"])
        assert state["chat_history"][2] == 3
        assert state["chat_history"][3] == 4
    except Exception as e:
        raise e
    finally:
        await sqlite_persister_2.close()
