from burr.integrations import base

try:
    import psycopg2
except ImportError as e:
    base.require_plugin(e, ["psycopg2"], "postgresql")

import json
import logging
from typing import Literal, Optional

from burr.core import persistence, state

logger = logging.getLogger(__name__)


class PostgreSQLPersister(persistence.BaseStatePersister):
    """Class for PostgreSQL persistence of state. This is a simple implementation.

    To try it out locally with docker -- here's a command -- change the values as appropriate.

    .. code:: bash

        docker run --name local-psql \  # container name
                   -v local_psql_data:/SOME/FILE_PATH/ \  # mounting a volume for data persistence
                   -p 54320:5432 \  # port mapping
                   -e POSTGRES_PASSWORD=my_password \  # superuser password
                   -d postgres  # database name

    Then you should be able to create the class like this:

    .. code:: python

        p = PostgreSQLPersister.from_values("postgres", "postgres", "my_password",
                                           "localhost", 54320, table_name="burr_state")


    """

    @classmethod
    def from_config(cls, config: dict) -> "PostgreSQLPersister":
        """Creates a new instance of the PostgreSQLPersister from a configuration dictionary."""
        return cls.from_values(
            db_name=config["db_name"],
            user=config["user"],
            password=config["password"],
            host=config["host"],
            port=config["port"],
            table_name=config.get("table_name", "burr_state"),
        )

    @classmethod
    def from_values(
        cls,
        db_name: str,
        user: str,
        password: str,
        host: str,
        port: int,
        table_name: str = "burr_state",
    ):
        """Builds a new instance of the PostgreSQLPersister from the provided values.

        :param db_name: the name of the PostgreSQL database.
        :param user: the username to connect to the PostgreSQL database.
        :param password: the password to connect to the PostgreSQL database.
        :param host: the host of the PostgreSQL database.
        :param port: the port of the PostgreSQL database.
        :param table_name:  the table name to store things under.
        """
        connection = psycopg2.connect(
            dbname=db_name, user=user, password=password, host=host, port=port
        )
        return cls(connection, table_name)

    def __init__(self, connection, table_name: str = "burr_state", serde_kwargs: dict = None):
        """Constructor

        :param connection: the connection to the PostgreSQL database.
        :param table_name:  the table name to store things under.
        """
        self.table_name = table_name
        self.connection = connection
        self.serde_kwargs = serde_kwargs or {}

    def set_serde_kwargs(self, serde_kwargs: dict):
        """Sets the serde_kwargs for the persister."""
        self.serde_kwargs = serde_kwargs

    def create_table(self, table_name: str):
        """Helper function to create the table where things are stored."""
        cursor = self.connection.cursor()
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                partition_key TEXT NOT NULL,
                app_id TEXT NOT NULL,
                sequence_id INTEGER NOT NULL,
                position TEXT NOT NULL,
                status TEXT NOT NULL,
                state JSONB NOT NULL,
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
        """Creates the table"""
        self.create_table(self.table_name)

    def list_app_ids(self, partition_key: str, **kwargs) -> list[str]:
        """Lists the app_ids for a given partition_key."""
        cursor = self.connection.cursor()
        cursor.execute(
            f"SELECT DISTINCT app_id, created_at FROM {self.table_name} "
            f"WHERE partition_key = %s "
            f"ORDER BY created_at DESC",
            (partition_key,),
        )
        app_ids = [row[0] for row in cursor.fetchall()]
        return app_ids

    def load(
        self, partition_key: str, app_id: str, sequence_id: int = None, **kwargs
    ) -> Optional[persistence.PersistedStateData]:
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
                f"WHERE partition_key = %s "
                f"ORDER BY CREATED_AT DESC LIMIT 1",
                (partition_key,),
            )
        elif sequence_id is None:
            cursor.execute(
                f"SELECT position, state, sequence_id, app_id, created_at, status FROM {self.table_name} "
                f"WHERE partition_key = %s AND app_id = %s "
                f"ORDER BY sequence_id DESC LIMIT 1",
                (partition_key, app_id),
            )
        else:
            cursor.execute(
                f"SELECT position, state, seqeuence_id, app_id, created_at, status FROM {self.table_name} "
                f"WHERE partition_key = %s AND app_id = %s AND sequence_id = %s ",
                (partition_key, app_id, sequence_id),
            )
        row = cursor.fetchone()
        if row is None:
            return None
        _state = state.State.deserialize(row[1], **self.serde_kwargs)
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
        state: state.State,
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
        json_state = json.dumps(state.serialize(**self.serde_kwargs))
        cursor.execute(
            f"INSERT INTO {self.table_name} (partition_key, app_id, sequence_id, position, state, status) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (partition_key, app_id, sequence_id, position, json_state, status),
        )
        self.connection.commit()

    def __del__(self):
        # closes connection at end when things are being shutdown.
        self.connection.close()


if __name__ == "__main__":
    # test the PostgreSQLPersister class
    persister = PostgreSQLPersister.from_values(
        "postgres", "postgres", "my_password", "localhost", 54320, table_name="burr_state"
    )

    persister.initialize()
    persister.save("pk", "app_id", 1, "pos", state.State({"a": 1, "b": 2}), "completed")
    print(persister.list_app_ids("pk"))
    print(persister.load("pk", "app_id"))
