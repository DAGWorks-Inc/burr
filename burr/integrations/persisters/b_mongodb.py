import json
import logging
from datetime import datetime, timezone
from typing import Literal, Optional

from pymongo import MongoClient

from burr.core import persistence, state

logger = logging.getLogger(__name__)


class MongoDBPersister(persistence.BaseStatePersister):
    """A class used to represent a MongoDB Persister.

    Example usage:

    .. code-block:: python

       persister = MongoDBPersister(uri='mongodb://user:pass@localhost:27017', db_name='mydatabase', collection_name='mystates')
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
    """

    def __init__(
        self,
        uri="mongodb://localhost:27017",
        db_name="mydatabase",
        collection_name="mystates",
        serde_kwargs: dict = None,
    ):
        """Initializes the MongoDBPersister class."""
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]
        self.serde_kwargs = serde_kwargs or {}

    def list_app_ids(self, partition_key: str, **kwargs) -> list[str]:
        """List the app ids for a given partition key."""
        app_ids = self.collection.distinct("app_id", {"partition_key": partition_key})
        return app_ids

    def load(
        self, partition_key: str, app_id: str, sequence_id: int = None, **kwargs
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
        partition_key: str,
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

    def __del__(self):
        self.client.close()
