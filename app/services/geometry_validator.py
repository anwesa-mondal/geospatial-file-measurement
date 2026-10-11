from enum import Enum
from typing import NamedTuple, Optional
from shapely.geometry.base import BaseGeometry
from shapely.validation import explain_validity

class ValidationStatus(str, Enum):
    VALID = "VALID"
    EMPTY_GEOMETRY = "EMPTY_GEOMETRY"
    INVALID_GEOMETRY = "INVALID_GEOMETRY"
    UNSUPPORTED_GEOMETRY = "UNSUPPORTED_GEOMETRY"

SUPPORTED_GEOMETRY_TYPES = {
    "Polygon",
    "MultiPolygon",
    "LineString",
    "MultiLineString",
    "Point",
    "MultiPoint"
}

class ValidationResult(NamedTuple):
    status: ValidationStatus
    geometry_type: Optional[str]
    message: Optional[str]
    geometry: Optional[BaseGeometry]

class GeometryValidator:
    @staticmethod
    def validate_geometry(geometry: Optional[BaseGeometry]) -> ValidationResult:
        if geometry is None:
            return ValidationResult(
                status=ValidationStatus.EMPTY_GEOMETRY,
                geometry_type=None,
                message="Geometry is missing or null.",
                geometry=None
            )

        if geometry.is_empty:
            geom_type = getattr(geometry, "geom_type", None)
            return ValidationResult(
                status=ValidationStatus.EMPTY_GEOMETRY,
                geometry_type=geom_type,
                message="Geometry is empty.",
                geometry=geometry
            )

        geom_type = geometry.geom_type
        if geom_type not in SUPPORTED_GEOMETRY_TYPES:
            return ValidationResult(
                status=ValidationStatus.UNSUPPORTED_GEOMETRY,
                geometry_type=geom_type,
                message=f"Unsupported geometry type: {geom_type}",
                geometry=geometry
            )

        if not geometry.is_valid:
            reason = explain_validity(geometry)
            return ValidationResult(
                status=ValidationStatus.INVALID_GEOMETRY,
                geometry_type=geom_type,
                message=f"Invalid geometry: {reason}",
                geometry=geometry
            )

        return ValidationResult(
            status=ValidationStatus.VALID,
            geometry_type=geom_type,
            message=None,
            geometry=geometry
        )
