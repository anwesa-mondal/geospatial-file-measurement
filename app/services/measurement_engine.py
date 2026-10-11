from typing import NamedTuple, Optional
from pyproj import CRS, Geod
from shapely.geometry.base import BaseGeometry
from app.services.geometry_validator import ValidationStatus, ValidationResult

class MeasurementResult(NamedTuple):
    area_sq_m: Optional[float]
    perimeter_m: Optional[float]
    length_m: Optional[float]
    method: Optional[str]
    measurement_crs: Optional[str]

class MeasurementEngine:
    def __init__(self):
        
        self.geod = Geod(ellps="WGS84")

    def calculate_measurement(
        self,
        validation: ValidationResult,
        crs: Optional[CRS]
    ) -> MeasurementResult:
        
        if validation.status != ValidationStatus.VALID or validation.geometry is None:
            return MeasurementResult(
                area_sq_m=None,
                perimeter_m=None,
                length_m=None,
                method=None,
                measurement_crs=crs.to_string() if crs else None
            )

        geom = validation.geometry
        geom_type = validation.geometry_type

        
        if geom_type in ("Point", "MultiPoint"):
            return MeasurementResult(
                area_sq_m=None,
                perimeter_m=None,
                length_m=None,
                method="NONE",
                measurement_crs=crs.to_string() if crs else None
            )

        if crs is None:
            return MeasurementResult(
                area_sq_m=None,
                perimeter_m=None,
                length_m=None,
                method=None,
                measurement_crs=None
            )

        is_geographic = crs.is_geographic
        is_projected = crs.is_projected

        if geom_type in ("Polygon", "MultiPolygon"):
            if is_geographic:
                
                
                
                raw_area, raw_perimeter = self.geod.geometry_area_perimeter(geom)
                return MeasurementResult(
                    area_sq_m=round(abs(raw_area), 4),
                    perimeter_m=round(abs(raw_perimeter), 4),
                    length_m=None,
                    method="GEODESIC_WGS84",
                    measurement_crs=crs.to_string()
                )
            elif is_projected:
                
                return MeasurementResult(
                    area_sq_m=round(abs(geom.area), 4),
                    perimeter_m=round(abs(geom.length), 4),
                    length_m=None,
                    method="PROJECTED_PLANAR",
                    measurement_crs=crs.to_string()
                )

        elif geom_type in ("LineString", "MultiLineString"):
            if is_geographic:
                raw_length = self.geod.geometry_length(geom)
                return MeasurementResult(
                    area_sq_m=None,
                    perimeter_m=None,
                    length_m=round(abs(raw_length), 4),
                    method="GEODESIC_WGS84",
                    measurement_crs=crs.to_string()
                )
            elif is_projected:
                return MeasurementResult(
                    area_sq_m=None,
                    perimeter_m=None,
                    length_m=round(abs(geom.length), 4),
                    method="PROJECTED_PLANAR",
                    measurement_crs=crs.to_string()
                )

        return MeasurementResult(
            area_sq_m=None,
            perimeter_m=None,
            length_m=None,
            method="UNKNOWN",
            measurement_crs=crs.to_string() if crs else None
        )
