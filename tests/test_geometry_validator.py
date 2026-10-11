import pytest
from shapely.geometry import (
    Point,
    MultiPoint,
    LineString,
    MultiLineString,
    Polygon,
    MultiPolygon,
    GeometryCollection,
)
from app.services.geometry_validator import GeometryValidator, ValidationStatus

validator = GeometryValidator()

def test_validate_valid_point():
    pt = Point(10.0, 20.0)
    res = validator.validate_geometry(pt)
    assert res.status == ValidationStatus.VALID
    assert res.geometry_type == "Point"
    assert res.message is None

def test_validate_valid_linestring():
    line = LineString([(0, 0), (1, 1), (2, 2)])
    res = validator.validate_geometry(line)
    assert res.status == ValidationStatus.VALID
    assert res.geometry_type == "LineString"

def test_validate_valid_polygon():
    poly = Polygon([(0, 0), (0, 10), (10, 10), (10, 0), (0, 0)])
    res = validator.validate_geometry(poly)
    assert res.status == ValidationStatus.VALID
    assert res.geometry_type == "Polygon"

def test_validate_empty_geometry():
    empty_poly = Polygon()
    res = validator.validate_geometry(empty_poly)
    assert res.status == ValidationStatus.EMPTY_GEOMETRY
    assert "empty" in res.message.lower()

def test_validate_none_geometry():
    res = validator.validate_geometry(None)
    assert res.status == ValidationStatus.EMPTY_GEOMETRY
    assert "missing" in res.message.lower()

def test_validate_invalid_geometry_bowtie():
    
    invalid_poly = Polygon([(0, 0), (2, 2), (2, 0), (0, 2), (0, 0)])
    res = validator.validate_geometry(invalid_poly)
    assert res.status == ValidationStatus.INVALID_GEOMETRY
    assert "Self-intersection" in res.message

def test_validate_unsupported_geometry():
    gc = GeometryCollection([Point(0, 0), LineString([(0, 0), (1, 1)])])
    res = validator.validate_geometry(gc)
    assert res.status == ValidationStatus.UNSUPPORTED_GEOMETRY
    assert "Unsupported geometry type" in res.message
