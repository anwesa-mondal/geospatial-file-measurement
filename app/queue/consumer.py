import logging
import os
import uuid
from typing import Optional, List, Tuple, Dict, Any
import redis.asyncio as aioredis
from redis.exceptions import ResponseError

from app.queue.config import (
    REDIS_URL,
    STREAM_NAME,
    CONSUMER_GROUP,
    CONSUMER_NAME_PREFIX,
    DEFAULT_CLAIM_MIN_IDLE_MS
)

logger = logging.getLogger(__name__)

class StreamConsumer:
    """
    Consumes and claims jobs from Redis Streams using consumer groups.
    Enables crash resilience through message acknowledgment and auto-claiming of orphaned jobs.
    """

    def __init__(
        self,
        consumer_name: Optional[str] = None,
        redis_client: Optional[aioredis.Redis] = None,
        redis_url: str = REDIS_URL
    ):
        self.consumer_name = consumer_name or f"{CONSUMER_NAME_PREFIX}_{os.getpid()}_{uuid.uuid4().hex[:6]}"
        self._client = redis_client
        self._redis_url = redis_url

    async def get_client(self) -> aioredis.Redis:
        if self._client is None:
            self._client = aioredis.from_url(self._redis_url, decode_responses=True)
        return self._client

    async def ensure_group(self) -> None:
        """
        Ensures the consumer group and stream exist.
        """
        client = await self.get_client()
        try:
            await client.xgroup_create(
                name=STREAM_NAME,
                groupname=CONSUMER_GROUP,
                id="0",
                mkstream=True
            )
            logger.info(f"Created consumer group '{CONSUMER_GROUP}' on stream '{STREAM_NAME}'.")
        except ResponseError as e:
            if "BUSYGROUP" in str(e):
                logger.debug(f"Consumer group '{CONSUMER_GROUP}' already exists.")
            else:
                raise e

    async def read_new_jobs(
        self,
        count: int = 1,
        block_ms: int = 2000
    ) -> List[Tuple[str, Dict[str, str]]]:
        """
        Reads newly published jobs using XREADGROUP with ID '>'.
        Returns list of (message_id, fields).
        """
        client = await self.get_client()
        try:
            entries = await client.xreadgroup(
                groupname=CONSUMER_GROUP,
                consumername=self.consumer_name,
                streams={STREAM_NAME: ">"},
                count=count,
                block=block_ms
            )
            if not entries:
                return []

            
            results = []
            for _, stream_messages in entries:
                for msg_id, fields in stream_messages:
                    results.append((msg_id, fields))
            return results
        except Exception as e:
            logger.error(f"Error reading new jobs from stream: {e}")
            return []

    async def read_pending_autoclaim(
        self,
        min_idle_time_ms: int = DEFAULT_CLAIM_MIN_IDLE_MS,
        count: int = 10
    ) -> List[Tuple[str, Dict[str, str]]]:
        """
        Claims and returns pending messages that have been idle longer than min_idle_time_ms
        (e.g., left behind by crashed workers).
        """
        client = await self.get_client()
        try:
            
            autoclaim_res = await client.xautoclaim(
                name=STREAM_NAME,
                groupname=CONSUMER_GROUP,
                consumername=self.consumer_name,
                min_idle_time=min_idle_time_ms,
                start_id="0-0",
                count=count
            )
            if not autoclaim_res or len(autoclaim_res) < 2:
                return []

            claimed_messages = autoclaim_res[1]
            results = []
            for msg_id, fields in claimed_messages:
                if fields:  
                    results.append((msg_id, fields))
            if results:
                logger.info(f"Auto-claimed {len(results)} orphaned job(s) from PEL for worker {self.consumer_name}.")
            return results
        except Exception as e:
            logger.error(f"Error auto-claiming pending jobs: {e}")
            return []

    async def ack_job(self, message_id: str) -> None:
        """
        Acknowledges that a message has been successfully processed.
        """
        client = await self.get_client()
        await client.xack(STREAM_NAME, CONSUMER_GROUP, message_id)
        logger.info(f"Acknowledged message '{message_id}' on stream '{STREAM_NAME}'.")

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
