import math
from typing import Optional
from fastapi import APIRouter, File, UploadFile, Query, status

from app.repositories.file_repository import FileRepository
from app.services.measurement_service import MeasurementService
from app.api.contract.response.file_response import (
    FileResponse,
    PaginatedMeasurementsResponse
)

router = APIRouter()
file_repository = FileRepository()
measurement_service = MeasurementService(repository=file_repository)

@router.post("/", response_model=FileResponse, status_code=status.HTTP_201_CREATED)
async def upload_and_process_file(file: UploadFile = File(...)):
    return await measurement_service.upload_and_process_file(file)

@router.get("/{id}", response_model=FileResponse)
async def get_file_metadata(id: str):
    return await measurement_service.get_file_metadata(id)

@router.get("/{id}/measurements", response_model=PaginatedMeasurementsResponse)
async def get_file_measurements(
    id: str,
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=10, ge=1, le=500, description="Items per page"),
):
    return await measurement_service.get_file_measurements(id, page, page_size)
