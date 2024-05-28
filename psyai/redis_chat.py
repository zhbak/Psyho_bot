import json
import logging
from typing import List, Optional

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import (
    BaseMessage,
    message_to_dict,
    messages_from_dict,
)

from langchain_community.utilities.redis import get_client

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Any, List, Optional, Pattern
from urllib.parse import urlparse

import numpy as np

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from redis.client import Redis as RedisType


def _array_to_buffer(array: List[float], dtype: Any = np.float32) -> bytes:
    return np.array(array).astype(dtype).tobytes()


def _buffer_to_array(buffer: bytes, dtype: Any = np.float32) -> List[float]:
    return np.frombuffer(buffer, dtype=dtype).tolist()

logger = logging.getLogger(__name__)


def get_client(redis_url: str, **kwargs: Any) -> RedisType:
    """Get a redis client from the connection url given. This helper accepts
    urls for Redis server (TCP with/without TLS or UnixSocket) as well as
    Redis Sentinel connections.

    Redis Cluster is not supported.

    Before creating a connection the existence of the database driver is checked
    an and ValueError raised otherwise

    To use, you should have the ``redis`` python package installed.

    Example:
        .. code-block:: python

            from langchain_community.utilities.redis import get_client
            redis_client = get_client(
                redis_url="redis://username:password@localhost:6379"
                index_name="my-index",
                embedding_function=embeddings.embed_query,
            )

    To use a redis replication setup with multiple redis server and redis sentinels
    set "redis_url" to "redis+sentinel://" scheme. With this url format a path is
    needed holding the name of the redis service within the sentinels to get the
    correct redis server connection. The default service name is "mymaster". The
    optional second part of the path is the redis db number to connect to.

    An optional username or password is used for booth connections to the rediserver
    and the sentinel, different passwords for server and sentinel are not supported.
    And as another constraint only one sentinel instance can be given:

    Example:
        .. code-block:: python

            from langchain_community.utilities.redis import get_client
            redis_client = get_client(
                redis_url="redis+sentinel://username:password@sentinelhost:26379/mymaster/0"
                index_name="my-index",
                embedding_function=embeddings.embed_query,
            )
    """

    # Initialize with necessary components.
    try:
        import redis
    except ImportError:
        raise ImportError(
            "Could not import redis python package. "
            "Please install it with `pip install redis>=4.1.0`."
        )

    # connect to redis server from url, reconnect with cluster client if needed
    redis_client = redis.from_url(redis_url, **kwargs)
    if _check_for_cluster(redis_client):
        redis_client.close()
        redis_client = _redis_cluster_client(redis_url, **kwargs)
    return redis_client



class RedisChatMessageHistory(BaseChatMessageHistory):
    """Chat message history stored in a Redis database."""

    def __init__(
        self,
        session_id: str,
        url: str = "redis://localhost:6379/0",
        key_prefix: str = "message_store:",
        ttl: Optional[int] = None,
    ):
        try:
            import redis
        except ImportError:
            raise ImportError(
                "Could not import redis python package. "
                "Please install it with `pip install redis`."
            )

        try:
            self.redis_client = get_client(redis_url=url)
        except redis.exceptions.ConnectionError as error:
            logger.error(error)

        self.session_id = session_id
        self.key_prefix = key_prefix
        self.ttl = ttl

    @property
    def key(self) -> str:
        """Construct the record key to use"""
        return self.key_prefix + self.session_id

    @property
    def messages(self) -> List[BaseMessage]:  # type: ignore
        """Retrieve the messages from Redis"""
        _items = self.redis_client.lrange(self.key, 0, -1)
        items = [json.loads(m.decode("utf-8")) for m in _items[::-1]]
        messages = messages_from_dict(items)
        return messages

    def add_message(self, message: BaseMessage) -> None:
        """Append the message to the record in Redis"""
        self.redis_client.lpush(self.key, json.dumps(message_to_dict(message)))
        if self.ttl:
            self.redis_client.expire(self.key, self.ttl)

    def clear(self) -> None:
        """Clear session memory from Redis"""
        self.redis_client.delete(self.key)


def _check_for_cluster(redis_client: RedisType) -> bool:
    import redis

    try:
        cluster_info = redis_client.info("cluster")
        return cluster_info["cluster_enabled"] == 1
    except redis.exceptions.RedisError:
        return False


def _redis_cluster_client(redis_url: str, **kwargs: Any) -> RedisType:
    from redis.cluster import RedisCluster

    return RedisCluster.from_url(redis_url, **kwargs)
