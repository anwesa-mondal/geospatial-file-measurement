from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class FileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    file_size: int
    source_crs: Optional[str] = None
    feature_count: int
    status: str
    error_message: Optional[str] = None
    created_at: datetime

class MeasurementFeatureResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    feature_index: int
    geometry_type: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
    validation_status: str
    validation_message: Optional[str] = None
    area_sq_m: Optional[float] = None
    perimeter_m: Optional[float] = None
    length_m: Optional[float] = None
    measurement_method: Optional[str] = None
    measurement_crs: Optional[str] = None

class PaginatedMeasurementsResponse(BaseModel):
    items: List[MeasurementFeatureResponse]
    total: int
    page: int
    page_size: int
    pages: int
