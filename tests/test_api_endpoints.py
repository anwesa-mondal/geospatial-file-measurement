import io
import zipfile
import pytest
from httpx import AsyncClient, ASGITransport
import geopandas as gpd
from shapely.geometry import Polygon, LineString

from app.main import app
from app.db.database import init_db

import pytest_asyncio
import pandas as pd

@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    await init_db()
    yield
    from app.db.database import engine
    await engine.dispose()

@pytest.fixture
def valid_zip_shapefile_bytes() -> bytes:
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        poly1 = Polygon([(0, 0), (0, 100), (100, 100), (100, 0), (0, 0)])
        poly2 = Polygon([(200, 200), (200, 300), (300, 300), (300, 200), (200, 200)])
        gdf = gpd.GeoDataFrame(
            {"name": pd.Series(["Zone1", "Zone2"], dtype=object), "geometry": [poly1, poly2]},
            crs="EPSG:3857"
        )
        shp_file = tmp_path / "test.shp"
        gdf.to_file(shp_file)

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as zf:
            for f in tmp_path.iterdir():
                zf.write(f, arcname=f.name)
        buffer.seek(0)
        return buffer.getvalue()

@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "healthy"}

@pytest.mark.asyncio
async def test_upload_and_retrieve_flow(valid_zip_shapefile_bytes):
    from unittest.mock import patch
    from app.queue.producer import StreamProducer
    from app.api.controllers.geospatial_file_measurement_controller import measurement_service
    from pathlib import Path

    with patch.object(StreamProducer, "publish_job", return_value="1234-0"):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            
            files = {"file": ("test_layer.zip", valid_zip_shapefile_bytes, "application/zip")}
            resp = await client.post("/api/files/", files=files)
            assert resp.status_code == 201
            data = resp.json()
            assert "id" in data
            assert data["filename"] == "test_layer.zip"
            assert data["status"] in ("processing", "PROCESSING")
            file_id = data["id"]

            
            staged_files = list(Path("uploads").glob(f"{file_id}.*"))
            assert len(staged_files) == 1
            await measurement_service.process_staged_file(
                file_id=file_id,
                filename="test_layer.zip",
                file_size=len(valid_zip_shapefile_bytes),
                file_path=staged_files[0]
            )

            
            meta_resp = await client.get(f"/api/files/{file_id}")
            assert meta_resp.status_code == 200
            meta_data = meta_resp.json()
            assert meta_data["id"] == file_id
            assert meta_data["feature_count"] == 2

            meas_resp = await client.get(f"/api/files/{file_id}/measurements")
            assert meas_resp.status_code == 200
            meas_data = meas_resp.json()
            assert meas_data["total"] == 2
            assert len(meas_data["items"]) == 2

            item1 = meas_data["items"][0]
            assert item1["geometry_type"] == "Polygon"
            assert item1["validation_status"] == "VALID"
            assert item1["area_sq_m"] == pytest.approx(10000.0, rel=1e-4)
            assert item1["perimeter_m"] == pytest.approx(400.0, rel=1e-4)

            item2 = meas_data["items"][1]
            assert item2["geometry_type"] == "Polygon"
            assert item2["validation_status"] == "VALID"
            assert item2["area_sq_m"] == pytest.approx(10000.0, rel=1e-4)
            assert item2["perimeter_m"] == pytest.approx(400.0, rel=1e-4)

@pytest.mark.asyncio
async def test_nonexistent_file_retrieval():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/files/nonexistent-id")
        assert resp.status_code == 404

        meas_resp = await client.get("/api/files/nonexistent-id/measurements")
        assert meas_resp.status_code == 404

@pytest.mark.asyncio
async def test_upload_invalid_file_extension():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        files = {"file": ("notes.txt", b"Invalid content", "text/plain")}
        resp = await client.post("/api/files/", files=files)
        assert resp.status_code in (415, 400)
