import asyncio
import logging
import signal
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from app.db.database import init_db
from app.repositories.file_repository import FileRepository
from app.services.measurement_service import MeasurementService
from app.queue.consumer import StreamConsumer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
)
logger = logging.getLogger("geospatial_worker")

class Worker:
    """
    Background worker that consumes geospatial processing tasks from Redis Streams.
    Provides crash resilience by acknowledging messages only upon completion and
    auto-claiming pending messages abandoned by crashed instances.
    """

    def __init__(self):
        self.repository = FileRepository()
        self.measurement_service = MeasurementService(repository=self.repository)
        self.consumer = StreamConsumer()
        self.running = True

    def stop(self, *args):
        logger.info("Worker received shutdown signal. Stopping...")
        self.running = False

    async def run(self):
        logger.info("Starting Geospatial Background Worker...")
        
        await init_db()
        logger.info("Database initialized.")

        
        await self.consumer.ensure_group()
        logger.info("Redis Stream consumer group initialized.")

        while self.running:
            try:
                
                claimed_jobs = await self.consumer.read_pending_autoclaim(count=5)
                for msg_id, fields in claimed_jobs:
                    await self._process_job(msg_id, fields, is_recovery=True)

                
                new_jobs = await self.consumer.read_new_jobs(count=1, block_ms=2000)
                for msg_id, fields in new_jobs:
                    await self._process_job(msg_id, fields, is_recovery=False)

            except asyncio.CancelledError:
                break
            except Exception as loop_err:
                logger.error(f"Unexpected error in worker loop: {loop_err}", exc_info=True)
                await asyncio.sleep(2)

        await self.consumer.close()
        logger.info("Worker stopped cleanly.")

    async def _process_job(self, msg_id: str, fields: dict, is_recovery: bool = False):
        file_id = fields.get("file_id")
        filename = fields.get("filename", "unknown")
        file_size = int(fields.get("file_size", 0))
        file_path = fields.get("file_path")

        prefix = "[RECOVERED]" if is_recovery else "[NEW]"
        logger.info(f"{prefix} Processing job {file_id} ({filename}) from message {msg_id}")

        if not file_path or not Path(file_path).exists():
            logger.warning(f"File path '{file_path}' not found on disk. Marking failed and acknowledging.")
            await self.repository.mark_file_failed(
                file_id=file_id,
                error_message=f"File not found on worker filesystem: {file_path}",
                filename=filename,
                file_size=file_size
            )
            await self.consumer.ack_job(msg_id)
            return

        try:
            await self.measurement_service.process_staged_file(
                file_id=file_id,
                filename=filename,
                file_size=file_size,
                file_path=file_path
            )
            
            await self.consumer.ack_job(msg_id)
            logger.info(f"Successfully finished job {file_id}")
        except Exception as proc_err:
            logger.error(f"Failed to process job {file_id}: {proc_err}")
            
            await self.consumer.ack_job(msg_id)

def main():
    worker = Worker()

    
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(sig, worker.stop)
        except (AttributeError, ValueError):
            pass

    asyncio.run(worker.run())

if __name__ == "__main__":
    main()
