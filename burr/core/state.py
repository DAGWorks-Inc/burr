import abc
import copy
import dataclasses
import json
import logging
import sqlite3
from typing import Any, Dict, Iterator, Literal, Mapping, Optional, TypedDict

logger = logging.getLogger(__name__)


class StateDelta(abc.ABC):
    """Represents a delta operation for state. This represents a transaction.
    Note it has the ability to mutate state in-place, but will be layered behind an immutable
    state object."""

    @classmethod
    @abc.abstractmethod
    def name(cls) -> str:
        """Unique name of this operation for ser/deser"""
        pass

    def serialize(self) -> dict:
        """Converts the state delta to a JSON object"""
        if not dataclasses.is_dataclass(self):
            raise TypeError("serialize method is only supported for dataclass instances")
        return dataclasses.asdict(self)

    def base_serialize(self) -> dict:
        """Converts the state delta to a JSON object"""
        return {"name": self.name(), "operation": self.serialize()}

    @classmethod
    def deserialize(cls, json_dict: dict) -> "StateDelta":
        """Converts a JSON object to a state delta"""
        if not dataclasses.is_dataclass(cls):
            raise TypeError("deserialize method is only supported for dataclass types")
        return cls(**json_dict)  # Assumes all fields in the dataclass match keys in json_dict

    def base_deserialize(self, json_dict: dict) -> "StateDelta":
        """Converts a JSON object to a state delta"""
        return self.deserialize(json_dict)

    @abc.abstractmethod
    def reads(self) -> list[str]:
        """Returns the keys that this state delta reads"""
        pass

    @abc.abstractmethod
    def writes(self) -> list[str]:
        """Returns the keys that this state delta writes"""
        pass

    @abc.abstractmethod
    def apply_mutate(self, inputs: dict):
        """Applies the state delta to the inputs"""
        pass


@dataclasses.dataclass
class SetFields(StateDelta):
    """State delta that sets fields in the state"""

    values: Mapping[str, Any]

    @classmethod
    def name(cls) -> str:
        return "set"

    def reads(self) -> list[str]:
        return list(self.values.keys())

    def writes(self) -> list[str]:
        return list(self.values.keys())

    def apply_mutate(self, inputs: dict):
        inputs.update(self.values)


@dataclasses.dataclass
class AppendFields(StateDelta):
    """State delta that appends to fields in the state"""

    values: Mapping[str, Any]

    @classmethod
    def name(cls) -> str:
        return "append"

    def reads(self) -> list[str]:
        return list(self.values.keys())

    def writes(self) -> list[str]:
        return list(self.values.keys())

    def apply_mutate(self, inputs: dict):
        for key, value in self.values.items():
            if key not in inputs:
                inputs[key] = []
            if not isinstance(inputs[key], list):
                raise ValueError(f"Cannot append to non-list value {key}={inputs[self.key]}")
            inputs[key].append(value)


@dataclasses.dataclass
class DeleteField(StateDelta):
    """State delta that deletes fields from the state"""

    keys: list[str]

    @classmethod
    def name(cls) -> str:
        return "delete"

    def reads(self) -> list[str]:
        return list(self.keys)

    def writes(self) -> list[str]:
        return []

    def apply_mutate(self, inputs: dict):
        for key in self.keys:
            inputs.pop(key, None)
        print(inputs)


class State(Mapping):
    """An immutable state object. Things to consider:
    1. Adding hooks on change
    2. Pulling/pushing to external places
    3. Simultaneous writes/reads in the case of parallelism
    4. Schema enforcement -- how to specify/manage? Should this be a
    dataclass when implemented?
    """

    def __init__(self, initial_values: Dict[str, Any] = None):
        if initial_values is None:
            initial_values = dict()
        self._state = initial_values

    def apply_operation(self, operation: StateDelta) -> "State":
        """Applies a given operation to the state, returning a new state"""
        new_state = copy.deepcopy(self._state)  # TODO -- restrict to just the read keys
        operation.apply_mutate(
            new_state
        )  # todo -- validate that the write keys are the only different ones
        return State(new_state)

    def get_all(self) -> Dict[str, Any]:
        """Returns the entire state, realize as a dictionary. This is a copy."""
        return dict(self)

    def update(self, **updates: Any) -> "State":
        """Updates the state with a set of key-value pairs"""
        return self.apply_operation(SetFields(updates))

    def append(self, **updates: Any) -> "State":
        """For each pair specified, appends to a list in state."""

        return self.apply_operation(AppendFields(updates))

    def wipe(self, delete: list[str] = None, keep: list[str] = None):
        """Wipes the state, either by deleting the keys in delete and keeping everything else
         or keeping the keys in keep. and deleting everything else. If you pass nothing in
         it will delete the whole thing.

        :param delete:
        :param keep:
        :return:
        """
        if delete is not None and keep is not None:
            raise ValueError(
                f"You cannot specify both delete and keep -- not both! "
                f"You have specified: delete={delete}, keep={keep}"
            )
        if delete is not None:
            fields_to_delete = delete
        else:
            fields_to_delete = [key for key in self._state if key not in keep]
        return self.apply_operation(DeleteField(fields_to_delete))

    def merge(self, other: "State") -> "State":
        """Merges two states together, overwriting the values in self
        with those in other."""
        return State({**self.get_all(), **other.get_all()})

    def subset(self, *keys: str, ignore_missing: bool = True) -> "State":
        """Returns a subset of the state, with only the given keys"""
        return State({key: self[key] for key in keys if key in self or not ignore_missing})

    def __getitem__(self, __k: str) -> Any:
        return self._state[__k]

    def __len__(self) -> int:
        return len(self._state)

    def __iter__(self) -> Iterator[Any]:
        return iter(self._state)

    def __repr__(self):
        return self.get_all().__repr__()  # quick hack


class PersistenceDict(TypedDict):
    partition_key: str
    app_id: str
    sequence_id: int
    position: str
    state: State
    created_at: str
    status: str


class BasicStatePersistence(abc.ABC):
    """Basic Interface for state persistence.

    A persister's job is to store and retrieve state.
    """

    def initialize(self):
        """Initializes the persistence."""
        pass

    @abc.abstractmethod
    def list_app_ids(self, partition_key: str) -> list[str]:
        """Returns list of app IDs for a given primary key"""
        pass

    @abc.abstractmethod
    def load(
        self, partition_key: str, app_id: Optional[str], sequence_id: Optional[int] = None
    ) -> Optional[PersistenceDict]:
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
    def save(
        self,
        partition_key: Optional[str],
        app_id: str,
        sequence_id: int,
        position: str,
        state: State,
        status: Literal["completed", "failed"],
    ):
        """Saves the state for a given app_id, sequence_id, position

        (PK, App_id, sequence_id, position) are a unique identifier for the state. Why not just
        (PK, App_id, sequence_id)? Because we're over-engineering this here. We're always going to have
        a position so might as well make it a quadruple.

        :param partition_key: the partition key. Note this could be None, but it's up to the persistor to whether
            that is a valid value it can handle.
        :param app_id:
        :param sequence_id:
        :param position:
        :param state:
        :param status:
        """
        pass


class SQLLitePersistence(BasicStatePersistence):
    """Class for SQLLite persistence of state. This is a simple implementation that uses SQLLite."""

    def __init__(self, db_path: str, table_name: str = "burr_state"):
        """Constructor

        :param db_path: the path the DB will be stored.
        :param table_name:  the table name to store things under.
        """
        self.db_path = db_path
        self.table_name = table_name

    @staticmethod
    def create_table_if_not_exists(db_path: str, table_name: str):
        """Helper function to create the table where things are stored if it doesn't exist."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

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
        conn.commit()
        conn.close()

    def initialize(self):
        """Creates the table if it doesn't exist"""
        # Usage
        self.create_table_if_not_exists(self.db_path, self.table_name)

    def list_app_ids(self, partition_key: str) -> list[str]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT DISTINCT app_id FROM {self.table_name} "
            f"WHERE partition_key = ? "
            f"ORDER BY created_at DESC",
            (partition_key,),
        )
        app_ids = [row[0] for row in cursor.fetchall()]
        conn.close()
        return app_ids

    def load(
        self, partition_key: str, app_id: str, sequence_id: int = None
    ) -> Optional[PersistenceDict]:
        """Loads state for a given partition id.

        Depending on the parameters, this will return the last thing written, the last thing written for a given app_id,
        or a specific sequence_id for a given app_id.

        :param partition_key:
        :param app_id:
        :param sequence_id:
        :return:
        """
        logger.debug("Loading %s, %s, %s", partition_key, app_id, sequence_id)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
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
        conn.close()
        if row is None:
            return None
        _state = State(json.loads(row[1])["_state"])
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
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        json_state = json.dumps(state.__dict__)
        cursor.execute(
            f"INSERT INTO {self.table_name} (partition_key, app_id, sequence_id, position, state, status) "
            f"VALUES (?, ?, ?, ?, ?, ?)",
            (partition_key, app_id, sequence_id, position, json_state, status),
        )
        conn.commit()
        conn.close()


if __name__ == "__main__":
    s = SQLLitePersistence(db_path=".sqllite.db", table_name="test1")
    s.initialize()
    s.save("pk", "app_id", 1, "pos", State({"a": 1, "b": 2}))
    print(s.list_app_ids("pk"))
    print(s.load("pk", "app_id"))
