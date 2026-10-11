import io
import zipfile
import pytest
import geopandas as gpd
from shapely.geometry import Polygon, Point
from app.services.measurement_service import MeasurementService
from app.api.exceptions.global_exception_handler import InvalidFileException

parser = MeasurementService()

def test_parse_nonexistent_file(tmp_path):
    fake_path = tmp_path / "does_not_exist.kml"
    with pytest.raises(InvalidFileException) as exc:
        parser.parse_file(fake_path)
    assert exc.value.status_code == 404

def test_parse_unsupported_format(tmp_path):
    text_file = tmp_path / "sample.txt"
    text_file.write_text("Hello world")
    with pytest.raises(InvalidFileException) as exc:
        parser.parse_file(text_file)
    assert exc.value.status_code == 415

def test_parse_corrupt_zip(tmp_path):
    bad_zip = tmp_path / "corrupt.zip"
    bad_zip.write_bytes(b"not a zip file content")
    with pytest.raises(InvalidFileException) as exc:
        parser.parse_file(bad_zip)
    assert exc.value.status_code == 400

def test_parse_zip_missing_shp_components(tmp_path):
    incomplete_zip = tmp_path / "missing_shx.zip"
    with zipfile.ZipFile(incomplete_zip, "w") as zf:
        zf.writestr("test.shp", b"dummy")
        
    with pytest.raises(InvalidFileException) as exc:
        parser.parse_file(incomplete_zip)
    assert "missing mandatory component" in exc.value.detail.lower()

def test_parse_valid_zip_shapefile(tmp_path):
    
    shp_dir = tmp_path / "raw_shp"
    shp_dir.mkdir()
    poly = Polygon([(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)])
    import pandas as pd
    gdf = gpd.GeoDataFrame({"name": pd.Series(["TestZone"], dtype=object), "geometry": [poly]}, crs="EPSG:4326")
    shp_file = shp_dir / "test.shp"
    gdf.to_file(shp_file)

    
    zip_path = tmp_path / "valid_shapefile.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        for f in shp_dir.iterdir():
            zf.write(f, arcname=f.name)

    parsed_gdf = parser.parse_file(zip_path)
    assert len(parsed_gdf) == 1
    assert parsed_gdf.crs.to_epsg() == 4326
    assert parsed_gdf.iloc[0]["name"] == "TestZone"
