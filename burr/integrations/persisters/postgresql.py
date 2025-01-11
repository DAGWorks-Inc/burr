"""This module is depricated. Please import from b_psycopg2.py."""

from burr.integrations import base
from burr.integrations.persisters.b_psycopg2 import PostgreSQLPersister as Psycopg2Persister

try:
    import psycopg2
except ImportError as e:
    base.require_plugin(e, "postgresql")


import logging

from burr.core import state

logger = logging.getLogger(__name__)
logger.warning(
    "This class is deprecated and has been moved. "
    "Please import PostgreSQLPersister from b_psycopg2.py."
)


class PostgreSQLPersister(Psycopg2Persister):
    """A class used to represent the Postgresql Persister.

    This class is deprecated and has been moved to b_psycopg2.py.
    """

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
        return Psycopg2Persister(connection, table_name)


if __name__ == "__main__":
    # test the PostgreSQLPersister class
    persister = PostgreSQLPersister.from_values(
        "postgres", "postgres", "my_password", "localhost", 54320, table_name="burr_state"
    )

    persister.initialize()
    persister.save("pk", "app_id", 1, "pos", state.State({"a": 1, "b": 2}), "completed")
    print(persister.list_app_ids("pk"))
    print(persister.load("pk", "app_id"))
