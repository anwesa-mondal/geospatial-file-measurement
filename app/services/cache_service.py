import logging
from typing import Optional
import redis.asyncio as aioredis
from app.queue.config import REDIS_URL

logger = logging.getLogger(__name__)

class CacheService:
    """
    Redis caching service for storing and retrieving serialized responses.
    Fails safely on network/connection errors so API requests fall back to database queries.
    """

    def __init__(self, redis_client: Optional[aioredis.Redis] = None, redis_url: str = REDIS_URL):
        self._client = redis_client
        self._redis_url = redis_url

    async def get_client(self) -> aioredis.Redis:
        if self._client is None:
            self._client = aioredis.from_url(self._redis_url, decode_responses=True)
        return self._client

    async def get(self, key: str) -> Optional[str]:
        """
        Fetch string/JSON value from Redis cache.
        Returns None on cache miss or if Redis is unreachable.
        """
        try:
            client = await self.get_client()
            return await client.get(key)
        except Exception as e:
            logger.warning(f"Cache GET error for key '{key}': {e}")
            return None

    async def set(self, key: str, value: str, ex: int = 3600) -> None:
        """
        Set key-value pair in Redis cache with an expiration time in seconds (default: 3600s / 1hr).
        """
        try:
            client = await self.get_client()
            await client.set(key, value, ex=ex)
        except Exception as e:
            logger.warning(f"Cache SET error for key '{key}': {e}")

    async def delete(self, key: str) -> None:
        """
        Delete a cached key from Redis.
        """
        try:
            client = await self.get_client()
            await client.delete(key)
        except Exception as e:
            logger.warning(f"Cache DELETE error for key '{key}': {e}")

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
