from burr.integrations import base

try:
    import redis  # can't name module redis because this import wouldn't work.

except ImportError as e:
    base.require_plugin(e, "redis")

import json
import logging
from datetime import datetime, timezone
from typing import Any, Literal, Optional

from burr.core import persistence, state

logger = logging.getLogger(__name__)


class RedisBasePersister(persistence.BaseStatePersister):
    """Main class for Redis persister.

    Use this class if you want to directly control injecting the Redis client.

    This class is responsible for persisting state data to a Redis database.
    It inherits from the BaseStatePersister class.

    Note: We didn't create the right constructor for the initial implementation of the RedisPersister class,
    so this is an attempt to fix that in a backwards compatible way.
    """

    @classmethod
    def default_client(cls) -> Any:
        """Returns the default client for the persister."""
        return redis.Redis

    @classmethod
    def from_values(
        cls,
        host: str,
        port: int,
        db: int,
        password: str = None,
        serde_kwargs: dict = None,
        redis_client_kwargs: dict = None,
        namespace: str = None,
    ) -> "RedisBasePersister":
        """Creates a new instance of the RedisBasePersister from passed in values."""
        if redis_client_kwargs is None:
            redis_client_kwargs = {}
        connection = cls.default_client()(
            host=host, port=port, db=db, password=password, **redis_client_kwargs
        )
        return cls(connection, serde_kwargs, namespace)

    def __init__(
        self,
        connection,
        serde_kwargs: dict = None,
        namespace: str = None,
    ):
        """Initializes the RedisPersister class.

        :param connection: the redis connection object.
        :param serde_kwargs: serialization and deserialization keyword arguments to pass to state SERDE.
        :param namespace: The name of the project to optionally use in the key prefix.
        """
        self.connection = connection
        self.serde_kwargs = serde_kwargs or {}
        self.namespace = namespace if namespace else ""

    def list_app_ids(self, partition_key: str, **kwargs) -> list[str]:
        """List the app ids for a given partition key."""
        namespaced_partition_key = (
            f"{self.namespace}:{partition_key}" if self.namespace else partition_key
        )
        app_ids = self.connection.zrevrange(namespaced_partition_key, 0, -1)
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
        namespaced_partition_key = (
            f"{self.namespace}:{partition_key}" if self.namespace else partition_key
        )
        if sequence_id is None:
            sequence_id = self.connection.zscore(namespaced_partition_key, app_id)
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
        namespaced_partition_key = (
            f"{self.namespace}:{partition_key}" if self.namespace else partition_key
        )
        self.connection.zadd(namespaced_partition_key, {app_id: sequence_id})

    def __del__(self):
        self.connection.close()

    def get_connection_params(self) -> dict:
        """Get the connection parameters for the Redis connection."""
        return {
            "host": self.connection.connection_pool.connection_kwargs["host"],
            "port": self.connection.connection_pool.connection_kwargs["port"],
            "db": self.connection.connection_pool.connection_kwargs["db"],
            "password": self.connection.connection_pool.connection_kwargs["password"],
        }

    def __getstate__(self) -> dict:
        state = self.__dict__.copy()
        # override self.get_connection_params if needed
        state["connection_params"] = self.get_connection_params()
        del state["connection"]
        return state

    def __setstate__(self, state: dict):
        connection_params = state.pop("connection_params")
        # override self.default_client if needed
        self.connection = self.default_client()(**connection_params)
        self.__dict__.update(state)


class RedisPersister(RedisBasePersister):
    """A class used to represent a Redis Persister.

    This class is deprecated. Use RedisBasePersister.from_values() instead.
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

        This is deprecated. Use RedisBasePersister.from_values() instead.

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
        connection = self.default_client()(
            host=host, port=port, db=db, password=password, **redis_client_kwargs
        )
        super(RedisPersister, self).__init__(connection, serde_kwargs, namespace)


if __name__ == "__main__":
    # test the RedisBasePersister class
    persister = RedisBasePersister.from_values("localhost", 6379, 0)

    persister.initialize()
    persister.save("pk", "app_id", 2, "pos", state.State({"a": 1, "b": 2}), "completed")
    print(persister.list_app_ids("pk"))
    print(persister.load("pk", "app_id"))
