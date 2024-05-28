import json
import logging
from typing import List, Optional

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import (
    BaseMessage,
    message_to_dict,
    messages_from_dict,
)


import logging, asyncio
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
        return self.key_prefix + self.session_id

    @property
    def messages(self):
        return asyncio.run_coroutine_threadsafe(self.aget_messages(), self.loop).result()

    async def aget_messages(self) -> List[BaseMessage]:  # type: ignore
        _items = await self.redis_client.lrange(self.key, 0, -1)
        items = [json.loads(m.decode("utf-8")) for m in _items[::-1]]
        messages = messages_from_dict(items)
        return messages

    def add_message(self, message: BaseMessage) -> None:
        asyncio.run_coroutine_threadsafe(self.aadd_message(message), self.loop)

    async def aadd_message(self, message: BaseMessage) -> None:
        await self.redis_client.lpush(self.key, json.dumps(message_to_dict(message)))
        if self.ttl:
            await self.redis_client.expire(self.key, self.ttl)

    def clear(self):
        asyncio.run_coroutine_threadsafe(self.aclear(), self.loop)

    async def aclear(self) -> None:
        await self.redis_client.delete(self.key)