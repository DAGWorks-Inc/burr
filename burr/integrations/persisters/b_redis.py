from burr.integrations import base

try:
    import redis  # can't name module redis because this import wouldn't work.

except ImportError as e:
    base.require_plugin(e, ["redis"], "redis")

import json
import logging
from datetime import datetime, timezone
from typing import Literal, Optional

from burr.core import persistence, state

logger = logging.getLogger(__name__)


class RedisPersister(persistence.BaseStatePersister):
    """A class used to represent a Redis Persister.

    This class is responsible for persisting state data to a Redis database.
    It inherits from the BaseStatePersister class.
    """

    def __init__(
        self,
        host: str,
        port: int,
        db: int,
        password: str = None,
        serde_kwargs: dict = None,
        redis_client_kwargs: dict = None,
        namespace: str = None,
    ):
        """Initializes the RedisPersister class.

        :param host:
        :param port:
        :param db:
        :param password:
        :param serde_kwargs:
        :param redis_client_kwargs: Additional keyword arguments to pass to the redis.Redis client.
        :param namespace: The name of the project to optionally use in the key prefix.
        """
        if redis_client_kwargs is None:
            redis_client_kwargs = {}
        self.connection = redis.Redis(
            host=host, port=port, db=db, password=password, **redis_client_kwargs
        )
        self.serde_kwargs = serde_kwargs or {}
        self.namespace = namespace if namespace else ""

    def list_app_ids(self, partition_key: str, **kwargs) -> list[str]:
        """List the app ids for a given partition key."""
        if self.namespace:
            app_ids = self.connection.zrevrange(f"{self.namespace}:{partition_key}", 0, -1)
        else:
            app_ids = self.connection.zrevrange(partition_key, 0, -1)
        return [app_id.decode() for app_id in app_ids]

    def load(
        self, partition_key: str, app_id: str, sequence_id: int = None, **kwargs
    ) -> Optional[persistence.PersistedStateData]:
        """Load the state data for a given partition key, app id, and sequence id.

        If the sequence id is not given, it will be looked up in the Redis database. If it is not found, None will be returned.

        :param partition_key:
        :param app_id:
        :param sequence_id:
        :param kwargs:
        :return: Value or None.
        """
        if sequence_id is None:
            if self.namespace:
                sequence_id = self.connection.zscore(f"{self.namespace}:{partition_key}", app_id)
            else:
                sequence_id = self.connection.zscore(partition_key, app_id)
            if sequence_id is None:
                return None
            sequence_id = int(sequence_id)
        key = self.create_key(app_id, partition_key, sequence_id)
        data = self.connection.hgetall(key)
        if not data:
            return None
        _state = state.State.deserialize(json.loads(data[b"state"].decode()), **self.serde_kwargs)
        return {
            "partition_key": partition_key,
            "app_id": app_id,
            "sequence_id": sequence_id,
            "position": data[b"position"].decode(),
            "state": _state,
            "created_at": data[b"created_at"].decode(),
            "status": data[b"status"].decode(),
        }

    def create_key(self, app_id, partition_key, sequence_id):
        """Create a key for the Redis database."""
        if self.namespace:
            key = f"{self.namespace}:{partition_key}:{app_id}:{sequence_id}"
        else:
            key = f"{partition_key}:{app_id}:{sequence_id}"
        return key

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
        """Save the state data to the Redis database.

        :param partition_key:
        :param app_id:
        :param sequence_id:
        :param position:
        :param state:
        :param status:
        :param kwargs:
        :return:
        """
        key = self.create_key(app_id, partition_key, sequence_id)
        if self.connection.exists(key):
            raise ValueError(f"partition_key:app_id:sequence_id[{key}] already exists.")
        json_state = json.dumps(state.serialize(**self.serde_kwargs))
        self.connection.hset(
            key,
            mapping={
                "partition_key": partition_key,
                "app_id": app_id,
                "sequence_id": sequence_id,
                "position": position,
                "state": json_state,
                "status": status,
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        if self.namespace:
            self.connection.zadd(f"{self.namespace}:{partition_key}", {app_id: sequence_id})
        else:
            self.connection.zadd(partition_key, {app_id: sequence_id})

    def __del__(self):
        self.connection.close()


if __name__ == "__main__":
    # test the RedisPersister class
    persister = RedisPersister("localhost", 6379, 0)

    persister.initialize()
    persister.save("pk", "app_id", 2, "pos", state.State({"a": 1, "b": 2}), "completed")
    print(persister.list_app_ids("pk"))
    print(persister.load("pk", "app_id"))
