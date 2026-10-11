from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import String, Integer, Float, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base

class FileRecord(Base):
    __tablename__ = "files"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    source_crs: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    feature_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="PROCESSING", nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    features: Mapped[List["FeatureRecord"]] = relationship(
        "FeatureRecord",
        back_populates="file",
        cascade="all, delete-orphan",
        order_by="FeatureRecord.feature_index"
    )

class FeatureRecord(Base):
    __tablename__ = "features"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    file_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("files.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    feature_index: Mapped[int] = mapped_column(Integer, nullable=False)
    geometry_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    properties: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    validation_status: Mapped[str] = mapped_column(String(50), nullable=False)
    validation_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    area_sq_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    perimeter_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    length_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    measurement_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    measurement_crs: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    file: Mapped["FileRecord"] = relationship("FileRecord", back_populates="features")
