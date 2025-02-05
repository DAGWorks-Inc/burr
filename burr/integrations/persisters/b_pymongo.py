import json
import logging
from datetime import datetime, timezone
from typing import Literal, Optional

from pymongo import MongoClient

from burr.core import persistence, state

logger = logging.getLogger(__name__)


class MongoDBBasePersister(persistence.BaseStatePersister):
    """A class used to represent a MongoDB Persister.

    Example usage:

    .. code-block:: python

       persister = MongoDBBasePersister.from_values(uri='mongodb://user:pass@localhost:27017',
                                                    db_name='mydatabase',
                                                    collection_name='mystates')
       persister.save(
           partition_key='example_partition',
           app_id='example_app',
           sequence_id=1,
           position='example_position',
           state=state.State({'key': 'value'}),
           status='completed'
       )
       loaded_state = persister.load(partition_key='example_partition', app_id='example_app', sequence_id=1)
       print(loaded_state)

    Note: this is called MongoDBBasePersister because we had to change the constructor and wanted to make
     this change backwards compatible.
    """

    @classmethod
    def from_config(cls, config: dict) -> "MongoDBBasePersister":
        """Creates a new instance of the MongoDBBasePersister from a configuration dictionary."""
        return cls.from_values(**config)

    @classmethod
    def from_values(
        cls,
        uri="mongodb://localhost:27017",
        db_name="mydatabase",
        collection_name="mystates",
        serde_kwargs: dict = None,
        mongo_client_kwargs: dict = None,
    ) -> "MongoDBBasePersister":
        """Initializes the MongoDBBasePersister class."""
        if mongo_client_kwargs is None:
            mongo_client_kwargs = {}
        client = MongoClient(uri, **mongo_client_kwargs)
        return cls(
            client=client,
            db_name=db_name,
            collection_name=collection_name,
            serde_kwargs=serde_kwargs,
        )

    def __init__(
        self,
        client,
        db_name="mydatabase",
        collection_name="mystates",
        serde_kwargs: dict = None,
    ):
        """Initializes the MongoDBBasePersister class.

        :param client: the mongodb client to use
        :param db_name: the name of the database to use
        :param collection_name: the name of the collection to use
        :param serde_kwargs: serializer/deserializer keyword arguments to pass to the state object
        """
        self.client = client
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]
        self.serde_kwargs = serde_kwargs or {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.connection.close()
        return False

    def set_serde_kwargs(self, serde_kwargs: dict):
        """Sets the serde_kwargs for the persister."""
        self.serde_kwargs = serde_kwargs

    def list_app_ids(self, partition_key: str, **kwargs) -> list[str]:
        """List the app ids for a given partition key."""
        app_ids = self.collection.distinct("app_id", {"partition_key": partition_key})
        return app_ids

    def load(
        self, partition_key: Optional[str], app_id: str, sequence_id: int = None, **kwargs
    ) -> Optional[persistence.PersistedStateData]:
        """Load the state data for a given partition key, app id, and sequence id."""
        query = {"partition_key": partition_key, "app_id": app_id}
        if sequence_id is not None:
            query["sequence_id"] = sequence_id
        document = self.collection.find_one(query, sort=[("sequence_id", -1)])
        if not document:
            return None
        _state = state.State.deserialize(json.loads(document["state"]), **self.serde_kwargs)
        return {
            "partition_key": partition_key,
            "app_id": app_id,
            "sequence_id": document["sequence_id"],
            "position": document["position"],
            "state": _state,
            "created_at": document["created_at"],
            "status": document["status"],
        }

    def save(
        self,
        partition_key: Optional[str],
        app_id: str,
        sequence_id: int,
        position: str,
        state: state.State,
        status: Literal["completed", "failed"],
        **kwargs,
    ):
        """Save the state data to the MongoDB database."""
        key = {"partition_key": partition_key, "app_id": app_id, "sequence_id": sequence_id}
        if self.collection.find_one(key):
            raise ValueError(f"partition_key:app_id:sequence_id[{key}] already exists.")
        json_state = json.dumps(state.serialize(**self.serde_kwargs))
        self.collection.insert_one(
            {
                "partition_key": partition_key,
                "app_id": app_id,
                "sequence_id": sequence_id,
                "position": position,
                "state": json_state,
                "status": status,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    def cleanup(self):
        """Closes the connection to the database."""
        self.connection.close()

    def __del__(self):
        # This should be deprecated -- using __del__ is unreliable for closing connections to db's;
        # the preferred way should be for the user to use a context manager or use the `.cleanup()`
        # method within a REST API framework.

        self.client.close()

    def __getstate__(self) -> dict:
        state = self.__dict__.copy()
        state["connection_params"] = {
            "uri": self.client.address[0],
            "port": self.client.address[1],
            "db_name": self.db.name,
            "collection_name": self.collection.name,
        }
        del state["client"]
        del state["db"]
        del state["collection"]
        return state

    def __setstate__(self, state: dict):
        connection_params = state.pop("connection_params")
        # we assume MongoClient.
        self.client = MongoClient(connection_params["uri"], connection_params["port"])
        self.db = self.client[connection_params["db_name"]]
        self.collection = self.db[connection_params["collection_name"]]
        self.__dict__.update(state)
