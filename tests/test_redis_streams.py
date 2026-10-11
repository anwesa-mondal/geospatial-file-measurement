import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.queue.producer import StreamProducer
from app.queue.consumer import StreamConsumer
from app.queue.config import STREAM_NAME, CONSUMER_GROUP

@pytest.mark.asyncio
async def test_stream_producer_publish():
    mock_redis = AsyncMock()
    mock_redis.xadd.return_value = "1720000000000-0"

    producer = StreamProducer(redis_client=mock_redis)
    msg_id = await producer.publish_job(
        file_id="test-uuid-123",
        filename="parcels.zip",
        file_size=1024,
        file_path="/uploads/test-uuid-123.zip"
    )

    assert msg_id == "1720000000000-0"
    mock_redis.xadd.assert_called_once_with(
        STREAM_NAME,
        {
            "file_id": "test-uuid-123",
            "filename": "parcels.zip",
            "file_size": "1024",
            "file_path": "/uploads/test-uuid-123.zip"
        }
    )

@pytest.mark.asyncio
async def test_stream_consumer_ensure_group():
    mock_redis = AsyncMock()
    consumer = StreamConsumer(consumer_name="worker_test_1", redis_client=mock_redis)

    await consumer.ensure_group()
    mock_redis.xgroup_create.assert_called_once_with(
        name=STREAM_NAME,
        groupname=CONSUMER_GROUP,
        id="0",
        mkstream=True
    )

@pytest.mark.asyncio
async def test_stream_consumer_read_and_ack():
    mock_redis = AsyncMock()
    mock_redis.xreadgroup.return_value = [
        [
            STREAM_NAME,
            [
                ("1720000000000-0", {"file_id": "job-1", "filename": "test.kml"})
            ]
        ]
    ]

    consumer = StreamConsumer(consumer_name="worker_test_1", redis_client=mock_redis)
    jobs = await consumer.read_new_jobs(count=1)

    assert len(jobs) == 1
    assert jobs[0][0] == "1720000000000-0"
    assert jobs[0][1]["file_id"] == "job-1"

    await consumer.ack_job("1720000000000-0")
    mock_redis.xack.assert_called_once_with(STREAM_NAME, CONSUMER_GROUP, "1720000000000-0")

@pytest.mark.asyncio
async def test_stream_consumer_autoclaim_crashed_jobs():
    mock_redis = AsyncMock()
    mock_redis.xautoclaim.return_value = [
        "0-0",
        [
            ("1720000000000-0", {"file_id": "crashed-job-99", "filename": "zone.zip"})
        ],
        []
    ]

    consumer = StreamConsumer(consumer_name="worker_test_1", redis_client=mock_redis)
    claimed = await consumer.read_pending_autoclaim(min_idle_time_ms=5000)

    assert len(claimed) == 1
    assert claimed[0][0] == "1720000000000-0"
    assert claimed[0][1]["file_id"] == "crashed-job-99"

@pytest.mark.asyncio
async def test_cache_service_get_set():
    from app.services.cache_service import CacheService
    mock_redis = AsyncMock()
    mock_redis.get.return_value = '{"items": [], "total": 0, "page": 1, "page_size": 50, "pages": 0}'

    cache = CacheService(redis_client=mock_redis)
    val = await cache.get("cache:key:1")
    assert val is not None
    mock_redis.get.assert_called_once_with("cache:key:1")

    await cache.set("cache:key:1", '{"test": true}', ex=3600)
    mock_redis.set.assert_called_once_with("cache:key:1", '{"test": true}', ex=3600)

@pytest.mark.asyncio
async def test_get_file_measurements_cache_hit():
    from app.services.measurement_service import MeasurementService
    from app.db.models import FileRecord
    from app.services.cache_service import CacheService

    mock_repo = AsyncMock()
    mock_repo.get_file_by_id.return_value = FileRecord(
        id="file-cache-1",
        filename="test.zip",
        file_size=100,
        status="completed"
    )

    mock_cache = AsyncMock()
    mock_cache.get.return_value = '{"items": [], "total": 0, "page": 1, "page_size": 50, "pages": 0}'

    service = MeasurementService(repository=mock_repo, cache_service=mock_cache)
    resp = await service.get_file_measurements("file-cache-1", page=1, page_size=50)

    assert resp.total == 0
    
    mock_repo.get_measurements_paginated.assert_not_called()
    mock_cache.get.assert_called_once_with("cache:measurements:file-cache-1:p1:s50")

