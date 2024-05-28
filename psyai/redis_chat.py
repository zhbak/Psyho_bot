import json
import logging
from typing import List, Optional

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import (
    BaseMessage,
    message_to_dict,
    messages_from_dict,
)


import logging
from typing import List, Optional


logger = logging.getLogger(__name__)


from redis.asyncio import ConnectionPool, Redis


class RedisChatMessageHistory(BaseChatMessageHistory):
    """Chat message history stored in a Redis database."""

    def __init__(
        self,
        session_id: str,
        pool: ConnectionPool,
        key_prefix: str = "message_store:",
        ttl: Optional[int] = None,
    ):
        self.redis_client = Redis(connection_pool=pool)
        self.session_id = session_id
        self.key_prefix = key_prefix
        self.ttl = ttl

    @property
    def key(self) -> str:
        """Construct the record key to use"""
        return self.key_prefix + self.session_id

    async def get_messages(self) -> List[BaseMessage]:
        """Retrieve the messages from Redis"""
        _items = await self.redis_client.lrange(self.key, 0, -1)
        items = [json.loads(m) for m in _items[::-1]]
        messages = messages_from_dict(items)
        return messages

    async def add_message(self, message: BaseMessage) -> None:
        """Append the message to the record in Redis"""
        await self.redis_client.lpush(self.key, json.dumps(message_to_dict(message)))
        if self.ttl:
            await self.redis_client.expire(self.key, self.ttl)

    async def clear(self) -> None:
        """Clear session memory from Redis"""
        await self.redis_client.delete(self.key)