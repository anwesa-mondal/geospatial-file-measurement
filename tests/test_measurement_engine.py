import pytest
from pyproj import CRS
from shapely.geometry import Polygon, LineString, Point
from app.services.geometry_validator import GeometryValidator
from app.services.measurement_engine import MeasurementEngine

engine = MeasurementEngine()
validator = GeometryValidator()

def test_measurement_point():
    pt = Point(10.0, 20.0)
    val = validator.validate_geometry(pt)
    res = engine.calculate_measurement(val, CRS.from_epsg(4326))
    assert res.area_sq_m is None
    assert res.perimeter_m is None
    assert res.length_m is None
    assert res.method == "NONE"

def test_measurement_projected_polygon():
    
    square = Polygon([(0, 0), (0, 100), (100, 100), (100, 0), (0, 0)])
    val = validator.validate_geometry(square)
    res = engine.calculate_measurement(val, CRS.from_epsg(3857))

    assert res.method == "PROJECTED_PLANAR"
    assert res.area_sq_m == pytest.approx(10000.0, rel=1e-4)
    assert res.perimeter_m == pytest.approx(400.0, rel=1e-4)
    assert res.length_m is None

def test_measurement_projected_linestring():
    
    line = LineString([(0, 0), (0, 500)])
    val = validator.validate_geometry(line)
    res = engine.calculate_measurement(val, CRS.from_epsg(3857))

    assert res.method == "PROJECTED_PLANAR"
    assert res.area_sq_m is None
    assert res.length_m == pytest.approx(500.0, rel=1e-4)

def test_measurement_geodesic_polygon():
    
    
    deg_poly = Polygon([(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)])
    val = validator.validate_geometry(deg_poly)
    res = engine.calculate_measurement(val, CRS.from_epsg(4326))

    assert res.method == "GEODESIC_WGS84"
    assert res.area_sq_m > 1.2e10
    assert res.perimeter_m > 400000.0

def test_measurement_geodesic_linestring():
    
    line = LineString([(0, 0), (1, 0)])
    val = validator.validate_geometry(line)
    res = engine.calculate_measurement(val, CRS.from_epsg(4326))

    assert res.method == "GEODESIC_WGS84"
    assert res.length_m == pytest.approx(111319.5, abs=50.0)

def test_measurement_invalid_geometry():
    bowtie = Polygon([(0, 0), (2, 2), (2, 0), (0, 2), (0, 0)])
    val = validator.validate_geometry(bowtie)
    res = engine.calculate_measurement(val, CRS.from_epsg(4326))

    assert res.area_sq_m is None
    assert res.perimeter_m is None
    assert res.length_m is None
