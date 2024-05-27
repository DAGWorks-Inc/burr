from pymongo import MongoClient
import datetime
import json
import logging
from typing import Literal, Optional
from burr.core import persistence, state
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class MongoDBPersister(persistence.BaseStatePersister):
    """A class used to represent a MongoDB Persister."""

    def __init__(self, uri='mongodb://localhost:27017', db_name='mydatabase', collection_name='mystates'):
        """Initializes the MongoDBPersister class."""
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

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
        _state = state.State(json.loads(document["state"]))
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
        json_state = json.dumps(state.get_all())
        self.collection.insert_one({
            "partition_key": partition_key,
            "app_id": app_id,
            "sequence_id": sequence_id,
            "position": position,
            "state": json_state,
            "status": status,
            "created_at": datetime.now(timezone.utc).isoformat(),

            # "created_at": datetime.datetime.utcnow().isoformat(),
        })

    def __del__(self):
        self.client.close()
