import abc
import json
import sqlite3
from abc import ABCMeta
from typing import Any, Dict, Literal, Optional, TypedDict

from burr.core import Action
from burr.core.state import State, logger
from burr.lifecycle import PostRunStepHook


class PersistedStateData(TypedDict):
    partition_key: str
    app_id: str
    sequence_id: int
    position: str
    state: State
    created_at: str
    status: str


class BaseStateLoader(abc.ABC):
    """Base class for state initialization. This goes together with a BaseStateSaver to form the
    database for your application."""

    @abc.abstractmethod
    def load(
        self, partition_key: str, app_id: Optional[str], sequence_id: Optional[int] = None, **kwargs
    ) -> Optional[PersistedStateData]:
        """Loads the state for a given app_id

        :param partition_key: the partition key. Note this could be None, but it's up to the persistor to whether
            that is a valid value it can handle.
        :param app_id: the identifier for the app instance being recorded.
        :param sequence_id: optional, the state corresponding to a specific point in time.
            If not provided, should return the latest.
        :return: position, state, sequence_id
        """
        pass

    @abc.abstractmethod
    def list_app_ids(self, partition_key: str, **kwargs) -> list[str]:
        """Returns list of app IDs for a given primary key"""
        pass


class BaseStateSaver(abc.ABC):
    """Basic Interface for state writing. This goes together with a BaseStateLoader to form the
    database for your application.
    """

    def initialize(self):
        """Initializes the app for saving, set up any databases, etc.. you want to here."""
        pass

    @abc.abstractmethod
    def save(
        self,
        partition_key: Optional[str],
        app_id: str,
        sequence_id: int,
        position: str,
        state: State,
        status: Literal["completed", "failed"],
        **kwargs,
    ):
        """Saves the state for a given app_id, sequence_id, position

        (PK, App_id, sequence_id, position) are a unique identifier for the state. Why not just
        (PK, App_id, sequence_id)? Because we're over-engineering this here. We're always going to have
        a position so might as well make it a quadruple.

        :param partition_key: the partition key. Note this could be None, but it's up to the persistor to whether
            that is a valid value it can handle.
        :param app_id: Appliaction UID to write with
        :param sequence_id: Sequence ID of the last executed step
        :param position: The action name that was implemented
        :param state: The current state of the application
        :param status: The status of this state, either "completed" or "failed". If "failed" the state is what it was
            before the action was applied.
        """
        pass


class BaseStatePersister(BaseStateLoader, BaseStateSaver, metaclass=ABCMeta):
    """Utility interface for a state reader/writer. This both persists and initializes state.
    Extend this class if you want an easy way to implement custom state storage.
    """

    pass


class PersisterHook(PostRunStepHook):
    """Wrapper class for bridging the persistence interface with lifecycle hooks. This is used internally."""

    def __init__(self, persister: BaseStateSaver):
        self.persister = persister

    def post_run_step(
        self,
        app_id: str,
        partition_key: str,
        sequence_id: int,
        state: "State",
        action: "Action",
        result: Optional[Dict[str, Any]],
        exception: Exception,
        **future_kwargs: Any,
    ):
        if exception is None:
            self.persister.save(partition_key, app_id, sequence_id, action.name, state, "completed")
        else:
            self.persister.save(partition_key, app_id, sequence_id, action.name, state, "failed")


class DevNullPersister(BaseStatePersister):
    """Does nothing, do not use this. This is for testing only."""

    def load(
        self, partition_key: str, app_id: Optional[str], sequence_id: Optional[int] = None, **kwargs
    ) -> Optional[PersistedStateData]:
        return None

    def list_app_ids(self, partition_key: str, **kwargs) -> list[str]:
        return []

    def save(
        self,
        partition_key: Optional[str],
        app_id: str,
        sequence_id: int,
        position: str,
        state: State,
        status: Literal["completed", "failed"],
        **kwargs,
    ):
        return


class SQLLitePersister(BaseStatePersister):
    """Class for SQLLite persistence of state. This is a simple implementation."""

    def __init__(self, db_path: str, table_name: str = "burr_state"):
        """Constructor

        :param db_path: the path the DB will be stored.
        :param table_name:  the table name to store things under.
        """
        self.db_path = db_path
        self.table_name = table_name
        self.connection = sqlite3.connect(db_path)

    def create_table_if_not_exists(self, table_name: str):
        """Helper function to create the table where things are stored if it doesn't exist."""
        cursor = self.connection.cursor()

        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                partition_key TEXT NOT NULL,
                app_id TEXT NOT NULL,
                sequence_id INTEGER NOT NULL,
                position TEXT NOT NULL,
                status TEXT NOT NULL,
                state TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (partition_key, app_id, sequence_id, position, state)
            )"""
        )
        cursor.execute(
            f"""
            CREATE INDEX IF NOT EXISTS {table_name}_created_at_index ON {table_name} (created_at);
        """
        )
        self.connection.commit()

    def initialize(self):
        """Creates the table if it doesn't exist"""
        # Usage
        self.create_table_if_not_exists(self.table_name)

    def list_app_ids(self, partition_key: str, **kwargs) -> list[str]:
        cursor = self.connection.cursor()
        cursor.execute(
            f"SELECT DISTINCT app_id FROM {self.table_name} "
            f"WHERE partition_key = ? "
            f"ORDER BY created_at DESC",
            (partition_key,),
        )
        app_ids = [row[0] for row in cursor.fetchall()]
        return app_ids

    def load(
        self, partition_key: str, app_id: str, sequence_id: int = None, **kwargs
    ) -> Optional[PersistedStateData]:
        """Loads state for a given partition id.

        Depending on the parameters, this will return the last thing written, the last thing written for a given app_id,
        or a specific sequence_id for a given app_id.

        :param partition_key:
        :param app_id:
        :param sequence_id:
        :return:
        """
        logger.debug("Loading %s, %s, %s", partition_key, app_id, sequence_id)
        cursor = self.connection.cursor()
        if app_id is None:
            # get latest for all app_ids
            cursor.execute(
                f"SELECT position, state, sequence_id, app_id, created_at, status FROM {self.table_name} "
                f"WHERE partition_key = ? "
                f"ORDER BY CREATED_AT DESC LIMIT 1",
                (partition_key,),
            )
        elif sequence_id is None:
            cursor.execute(
                f"SELECT position, state, sequence_id, app_id, created_at, status FROM {self.table_name} "
                f"WHERE partition_key = ? AND app_id = ? "
                f"ORDER BY sequence_id DESC LIMIT 1",
                (partition_key, app_id),
            )
        else:
            cursor.execute(
                f"SELECT position, state, seqeuence_id, app_id, created_at, status FROM {self.table_name} "
                f"WHERE partition_key = ? AND app_id = ? AND sequence_id = ?",
                (partition_key, app_id, sequence_id),
            )
        row = cursor.fetchone()
        if row is None:
            return None
        _state = State(json.loads(row[1]))
        return {
            "partition_key": partition_key,
            "app_id": row[3],
            "sequence_id": row[2],
            "position": row[0],
            "state": _state,
            "created_at": row[4],
            "status": row[5],
        }

    def save(
        self,
        partition_key: str,
        app_id: str,
        sequence_id: int,
        position: str,
        state: State,
        status: Literal["completed", "failed"],
        **kwargs,
    ):
        """
        Saves the state for a given app_id, sequence_id, and position.

        This method connects to the SQLite database, converts the state to a JSON string, and inserts a new record
        into the table with the provided partition_key, app_id, sequence_id, position, and state. After the operation,
        it commits the changes and closes the connection to the database.

        :param partition_key: The partition key. This could be None, but it's up to the persistor to whether
            that is a valid value it can handle.
        :param app_id: The identifier for the app instance being recorded.
        :param sequence_id: The state corresponding to a specific point in time.
        :param position: The position in the sequence of states.
        :param state: The state to be saved, an instance of the State class.
        :param status: The status of this state, either "completed" or "failed". If "failed" the state is what it was
            before the action was applied.
        :return: None
        """
        logger.debug(
            "saving %s, %s, %s, %s, %s, %s",
            partition_key,
            app_id,
            sequence_id,
            position,
            state,
            status,
        )
        cursor = self.connection.cursor()
        json_state = json.dumps(state.get_all())
        cursor.execute(
            f"INSERT INTO {self.table_name} (partition_key, app_id, sequence_id, position, state, status) "
            f"VALUES (?, ?, ?, ?, ?, ?)",
            (partition_key, app_id, sequence_id, position, json_state, status),
        )
        self.connection.commit()

    def __del__(self):
        # closes connection at end when things are being shutdown.
        self.connection.close()


if __name__ == "__main__":
    s = SQLLitePersister(db_path=".sqllite.db", table_name="test1")
    s.initialize()
    s.save("pk", "app_id", 1, "pos", State({"a": 1, "b": 2}), "completed")
    print(s.list_app_ids("pk"))
    print(s.load("pk", "app_id"))
