import logging
from typing import Optional
import redis.asyncio as aioredis
from app.queue.config import REDIS_URL, STREAM_NAME

logger = logging.getLogger(__name__)

class StreamProducer:
    """
    Publishes geospatial file ingestion events to Redis Streams.
    """

    def __init__(self, redis_client: Optional[aioredis.Redis] = None, redis_url: str = REDIS_URL):
        self._client = redis_client
        self._redis_url = redis_url

    async def get_client(self) -> aioredis.Redis:
        if self._client is None:
            self._client = aioredis.from_url(self._redis_url, decode_responses=True)
        return self._client

    async def publish_job(
        self,
        file_id: str,
        filename: str,
        file_size: int,
        file_path: str
    ) -> str:
        """
        Publishes a geospatial processing job to the Redis Stream.
        Returns the generated Redis message ID.
        """
        client = await self.get_client()
        payload = {
            "file_id": file_id,
            "filename": filename,
            "file_size": str(file_size),
            "file_path": str(file_path)
        }
        message_id = await client.xadd(STREAM_NAME, payload)
        logger.info(f"Published job {file_id} to stream '{STREAM_NAME}' (message ID: {message_id})")
        return message_id

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
