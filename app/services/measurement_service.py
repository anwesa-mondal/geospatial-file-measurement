import json
import logging
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import List, Optional, Union
import pandas as pd
import geopandas as gpd
from fastapi import status, UploadFile
import math

from app.db.models import FeatureRecord, FileRecord
from app.enums import Status
from app.repositories import FileRepository
from app.services.geometry_validator import GeometryValidator
from app.services.measurement_engine import MeasurementEngine
from app.services.upload_file_service import UploadFileService
from app.services.cache_service import CacheService
from app.queue.producer import StreamProducer
from app.api.contract.response.file_response import (
    MeasurementFeatureResponse,
    PaginatedMeasurementsResponse,
    FileResponse
)
from app.api.exceptions.global_exception_handler import InvalidFileException

logger = logging.getLogger(__name__)

class MeasurementService:
    """
    Coordinates geospatial processing:
    - Parses vector formats (KML and zipped ESRI Shapefiles) into GeoDataFrames
    - Validates geometries via GeometryValidator
    - Computes geometric measurements via MeasurementEngine
    - Persists lifecycle states and records via FileRepository
    - Queues jobs to Redis Streams for background worker execution
    - Caches completed paginated measurement responses in Redis
    """

    def __init__(
        self,
        repository: Optional[FileRepository] = None,
        validator: Optional[GeometryValidator] = None,
        measurement_engine: Optional[MeasurementEngine] = None,
        upload_file_service: Optional[UploadFileService] = None,
        stream_producer: Optional[StreamProducer] = None,
        cache_service: Optional[CacheService] = None,
    ):
        self.repository = repository or FileRepository()
        self.validator = validator or GeometryValidator()
        self.measurement_engine = measurement_engine or MeasurementEngine()
        self.upload_file_service = upload_file_service or UploadFileService()
        self.stream_producer = stream_producer or StreamProducer()
        self.cache_service = cache_service or CacheService()

    async def upload_and_process_file(
        self,
        file: UploadFile
    ) -> FileRecord:
        """
        Receives an uploaded file, stages it on disk, creates a PROCESSING record in DB,
        and queues the job via Redis Streams for asynchronous background worker processing.
        """
        extension = self.upload_file_service.validate_file_type(file)
        file_id, file_path, size = await self.upload_file_service.save_file(file, extension)
        filename = file.filename or "unknown"

        
        file_record = await self.repository.create_file(
            file_id=file_id,
            filename=filename,
            file_size=size,
            status=Status.PROCESSING
        )

        
        await self.stream_producer.publish_job(
            file_id=file_id,
            filename=filename,
            file_size=size,
            file_path=str(file_path)
        )

        try:
            resp_dto = FileResponse.model_validate(file_record)
            await self.cache_service.set(f"cache:meta:{file_id}", resp_dto.model_dump_json(), ex=60)
        except Exception as cache_err:
            logger.warning(f"Could not prime metadata cache: {cache_err}")

        return file_record

    async def process_staged_file(
        self,
        file_id: str,
        filename: str,
        file_size: int,
        file_path: Union[str, Path]
    ) -> FileRecord:
        """
        Worker-side processing function for staged files consumed from Redis Streams.
        """
        path = Path(file_path)
        try:
            file_record = await self.repository.get_file_by_id(file_id)
            if not file_record:
                file_record = await self.repository.create_file(
                    file_id=file_id,
                    filename=filename,
                    file_size=file_size,
                    status=Status.PROCESSING
                )
            return await self._process_existing_record(file_record, path)
        finally:
            self.upload_file_service.remove_file(path)

    async def _process_existing_record(
        self,
        file_record: FileRecord,
        path: Path
    ) -> FileRecord:
        """
        Executes file parsing, geometry validation, measurement calculation,
        and persists the completed results to PostgreSQL.
        """
        try:
            gdf = self._parse_file(path)
            source_crs_str = gdf.crs.to_string() if gdf.crs else None
            feature_count = len(gdf)
            feature_records = self._process_each_feature(file_record.id, gdf)

            updated_record = await self.repository.save_processed_file(
                file_id=file_record.id,
                source_crs=source_crs_str,
                feature_count=feature_count,
                feature_records=feature_records
            )

            try:
                resp_dto = FileResponse.model_validate(updated_record)
                await self.cache_service.set(f"cache:meta:{file_record.id}", resp_dto.model_dump_json(), ex=86400)
            except Exception as cache_err:
                logger.warning(f"Failed to update metadata cache: {cache_err}")

            return updated_record
        except Exception as e:
            logger.error(f"Error processing file {file_record.id}: {e}")
            failed_record = await self.repository.mark_file_failed(
                file_id=file_record.id,
                error_message=str(e),
                filename=file_record.filename,
                file_size=file_record.file_size
            )
            try:
                resp_dto = FileResponse.model_validate(failed_record)
                await self.cache_service.set(f"cache:meta:{file_record.id}", resp_dto.model_dump_json(), ex=86400)
            except Exception as cache_err:
                logger.warning(f"Failed to update metadata cache on failure: {cache_err}")
            raise e

    async def get_file_metadata(self, id: str) -> Union[FileRecord, dict]:
        cache_key = f"cache:meta:{id}"
        cached_json = await self.cache_service.get(cache_key)
        if cached_json:
            try:
                return FileResponse.model_validate_json(cached_json)
            except Exception as err:
                logger.warning(f"Error deserializing cached metadata: {err}")

        file_record = await self.repository.get_file_by_id(id)
        if not file_record:
            raise InvalidFileException(
                f"File with ID '{id}' was not found.",
                status.HTTP_404_NOT_FOUND
            )

        try:
            resp_dto = FileResponse.model_validate(file_record)
            ex = 86400 if str(file_record.status).lower() in ("completed", "failed") else 10
            await self.cache_service.set(cache_key, resp_dto.model_dump_json(), ex=ex)
        except Exception as cache_err:
            logger.warning(f"Failed to set metadata cache: {cache_err}")

        return file_record

    async def get_file_by_id(self, id: str) -> FileRecord:
        """Alias for get_file_metadata."""
        return await self.get_file_metadata(id)

    async def get_file_measurements(
        self,
        id: str,
        page: int = 1,
        page_size: int = 50
    ) -> PaginatedMeasurementsResponse:
        file_record = await self.repository.get_file_by_id(id)
        if not file_record:
            raise InvalidFileException(
                f"File with ID '{id}' was not found.",
                status.HTTP_404_NOT_FOUND
            )

        
        cache_key = f"cache:measurements:{id}:p{page}:s{page_size}"
        cached_json = await self.cache_service.get(cache_key)
        if cached_json:
            logger.info(f"Cache HIT for measurements {cache_key}")
            return PaginatedMeasurementsResponse.model_validate_json(cached_json)

        
        logger.debug(f"Cache MISS for measurements {cache_key}")
        features, total = await self.repository.get_measurements_paginated(
            file_id=id,
            page=page,
            page_size=page_size
        )

        pages = math.ceil(total / page_size) if total > 0 else 0

        response = PaginatedMeasurementsResponse(
            items=[MeasurementFeatureResponse.model_validate(f) for f in features],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages
        )

        
        status_str = str(file_record.status).lower()
        if status_str in (Status.COMPLETED.value.lower(), "completed"):
            await self.cache_service.set(cache_key, response.model_dump_json(), ex=3600)

        return response

    def parse_file(self, file_path: Union[str, Path]) -> gpd.GeoDataFrame:
        """Public parsing helper."""
        return self._parse_file(Path(file_path))

    def _parse_file(self, file_path: Union[str, Path]) -> gpd.GeoDataFrame:
        """
        Parses a vector geospatial file (.kml or .zip Shapefile) into a GeoDataFrame.
        """
        path = Path(file_path)
        if not path.exists():
            raise InvalidFileException(f"File not found: {path}", status.HTTP_404_NOT_FOUND)

        ext = path.suffix.lower()
        if ext == ".kml":
            gdf = self._parse_kml(path)
        elif ext == ".zip":
            gdf = self._parse_zip_shapefile(path)
        else:
            raise InvalidFileException(f"Unsupported file format: {ext}", status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

        if gdf.empty:
            raise InvalidFileException("The file contains no features", status.HTTP_404_NOT_FOUND)

        return gdf

    def _parse_kml(self, file_path: Path) -> gpd.GeoDataFrame:
        try:
            gdf = gpd.read_file(file_path, driver="KML")
        except Exception as e:
            logger.warning(f"Failed to read KML with default layer: {e}. Trying fiona layer inspection.")
            import fiona
            try:
                layers = fiona.listlayers(str(file_path))
                if not layers:
                    raise InvalidFileException("The KML file contains no readable layers.", status.HTTP_404_NOT_FOUND)
                gdf = gpd.read_file(file_path, driver="KML", layer=layers[0])
            except Exception as layer_err:
                raise InvalidFileException(f"Failed to parse KML file: {str(layer_err)}", status.HTTP_400_BAD_REQUEST)

        
        if gdf.crs is None:
            gdf.set_crs(epsg=4326, inplace=True)

        return gdf

    def _parse_zip_shapefile(self, file_path: Path) -> gpd.GeoDataFrame:
        if not zipfile.is_zipfile(file_path):
            raise InvalidFileException("The uploaded file is not a valid ZIP archive.", status.HTTP_400_BAD_REQUEST)

        extract_dir = Path(tempfile.mkdtemp(prefix="shp_extract_"))
        try:
            with zipfile.ZipFile(file_path, "r") as archive:
                
                for member in archive.infolist():
                    member_path = Path(member.filename)
                    if member_path.is_absolute() or ".." in member_path.parts:
                        raise InvalidFileException("Zip archive contains unsafe paths.", status.HTTP_400_BAD_REQUEST)

                archive.extractall(extract_dir)

            
            shp_files = list(extract_dir.rglob("*.shp"))
            if not shp_files:
                raise InvalidFileException("ZIP archive does not contain any Shapefile (.shp).", status.HTTP_404_NOT_FOUND)
            if len(shp_files) > 1:
                names = [f.name for f in shp_files]
                raise InvalidFileException(
                    f"ZIP archive contains multiple Shapefiles ({', '.join(names)}). Please provide a ZIP with a single Shapefile.",
                    status.HTTP_400_BAD_REQUEST
                )

            shp_file = shp_files[0]
            
            stem = shp_file.stem
            parent = shp_file.parent
            shx_exists = any(p.stem == stem and p.suffix.lower() == ".shx" for p in parent.iterdir())
            dbf_exists = any(p.stem == stem and p.suffix.lower() == ".dbf" for p in parent.iterdir())

            if not shx_exists or not dbf_exists:
                missing = []
                if not shx_exists:
                    missing.append(".shx")
                if not dbf_exists:
                    missing.append(".dbf")
                raise InvalidFileException(
                    f"Incomplete Shapefile: missing mandatory component(s) {', '.join(missing)}.",
                    status.HTTP_400_BAD_REQUEST
                )

            try:
                gdf = gpd.read_file(shp_file)
            except Exception as e:
                raise InvalidFileException(f"Failed to parse Shapefile: {str(e)}", status.HTTP_400_BAD_REQUEST)

            return gdf

        finally:
            shutil.rmtree(extract_dir, ignore_errors=True)

    def _process_each_feature(self, file_id: str, gdf: gpd.GeoDataFrame) -> List[FeatureRecord]:
        feature_records: List[FeatureRecord] = []
        prop_cols = [c for c in gdf.columns if c != gdf.geometry.name]

        for idx, row in gdf.iterrows():
            geom = row.geometry if hasattr(row, "geometry") else None
            validation = self.validator.validate_geometry(geom)
            measurement = self.measurement_engine.calculate_measurement(validation, gdf.crs)
            props = self._extract_serializable_properties(row, prop_cols)

            feat_record = FeatureRecord(
                file_id=file_id,
                feature_index=int(idx) if isinstance(idx, int) else len(feature_records),
                geometry_type=validation.geometry_type,
                properties=props,
                validation_status=validation.status.value,
                validation_message=validation.message,
                area_sq_m=measurement.area_sq_m,
                perimeter_m=measurement.perimeter_m,
                length_m=measurement.length_m,
                measurement_method=measurement.method,
                measurement_crs=measurement.measurement_crs
            )
            feature_records.append(feat_record)

        return feature_records

    def _extract_serializable_properties(self, row: pd.Series, prop_cols: List[str]) -> dict:
        props = {}
        for col in prop_cols:
            val = row[col]
            if pd.isna(val):
                props[col] = None
            elif hasattr(val, "isoformat"):
                props[col] = val.isoformat()
            else:
                try:
                    json.dumps(val)
                    props[col] = val
                except (TypeError, OverflowError):
                    props[col] = str(val)
        return props
