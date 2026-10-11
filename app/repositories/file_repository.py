from app.enums import Status
import logging
from contextlib import asynccontextmanager
from typing import Optional, List, Tuple, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.database import AsyncSessionLocal
from app.db.models import FileRecord, FeatureRecord

logger = logging.getLogger(__name__)

class FileRepository:
    """
    Repository layer responsible for all database interactions for FileRecord and FeatureRecord.
    The service layer communicates with this repository instead of calling the database directly.
    """

    def __init__(self, session: Optional[AsyncSession] = None):
        self._session = session

    @asynccontextmanager
    async def _session_scope(self):
        """Provide an active database session."""
        if self._session is not None:
            yield self._session
        else:
            async with AsyncSessionLocal() as session:
                yield session

    async def create_file(
        self,
        file_id: str,
        filename: str,
        file_size: int,
        status: Union[str, Status] = Status.PROCESSING.value
    ) -> FileRecord:
        """Create and persist an initial FileRecord."""
        status_val = status.value if isinstance(status, Status) else status
        async with self._session_scope() as session:
            file_record = FileRecord(
                id=file_id,
                filename=filename,
                file_size=file_size,
                feature_count=0,
                status=status_val
            )
            session.add(file_record)
            await session.commit()
            await session.refresh(file_record)
            return file_record

    async def save_processed_file(
        self,
        file_id: str,
        source_crs: Optional[str],
        feature_count: int,
        feature_records: List[FeatureRecord]
    ) -> FileRecord:
        """Atomically persist feature records and update file status to COMPLETED."""
        async with self._session_scope() as session:
            file_record = await session.get(FileRecord, file_id)
            if not file_record:
                file_record = FileRecord(
                    id=file_id,
                    filename="unknown",
                    file_size=0,
                    feature_count=feature_count,
                    source_crs=source_crs,
                    status=Status.COMPLETED.value
                )
                session.add(file_record)
            else:
                file_record.source_crs = source_crs
                file_record.feature_count = feature_count
                file_record.status = Status.COMPLETED.value

            session.add_all(feature_records)
            await session.commit()
            await session.refresh(file_record)
            return file_record

    async def mark_file_failed(
        self,
        file_id: str,
        error_message: str,
        filename: str = "unknown",
        file_size: int = 0
    ) -> FileRecord:
        """Persist FAILED status and error message for a file."""
        async with self._session_scope() as session:
            file_record = await session.get(FileRecord, file_id)
            if not file_record:
                file_record = FileRecord(
                    id=file_id,
                    filename=filename,
                    file_size=file_size,
                    status=Status.FAILED.value,
                    error_message=error_message
                )
                session.add(file_record)
            else:
                file_record.status = Status.FAILED.value
                file_record.error_message = error_message
            await session.commit()
            await session.refresh(file_record)
            return file_record

    async def get_file_by_id(self, file_id: str) -> Optional[FileRecord]:
        """Retrieve a FileRecord by ID."""
        async with self._session_scope() as session:
            result = await session.execute(select(FileRecord).where(FileRecord.id == file_id))
            return result.scalar_one_or_none()

    async def get_measurements_paginated(
        self,
        file_id: str,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[FeatureRecord], int]:
        """Retrieve paginated feature measurement records and total count."""
        async with self._session_scope() as session:
            count_query = select(func.count(FeatureRecord.id)).where(FeatureRecord.file_id == file_id)
            total_res = await session.execute(count_query)
            total = total_res.scalar() or 0

            offset = (page - 1) * page_size
            items_query = (
                select(FeatureRecord)
                .where(FeatureRecord.file_id == file_id)
                .order_by(FeatureRecord.feature_index)
                .offset(offset)
                .limit(page_size)
            )
            items_res = await session.execute(items_query)
            features = list(items_res.scalars().all())
            return features, total
