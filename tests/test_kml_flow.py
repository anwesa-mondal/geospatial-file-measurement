import io
import pytest
from httpx import AsyncClient, ASGITransport
import geopandas as gpd
from shapely.geometry import Polygon, LineString

from app.main import app
from app.db.database import init_db

@pytest.mark.asyncio
async def test_kml_upload_and_measurements():
    await init_db()

    
    kml_content = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <Placemark>
      <name>Test Square</name>
      <Polygon>
        <outerBoundaryIs>
          <LinearRing>
            <coordinates>
              0,0,0
              0,0.01,0
              0.01,0.01,0
              0.01,0,0
              0,0,0
            </coordinates>
          </LinearRing>
        </outerBoundaryIs>
      </Polygon>
    </Placemark>
    <Placemark>
      <name>Test Route</name>
      <LineString>
        <coordinates>
          0,0,0
          0.01,0,0
        </coordinates>
      </LineString>
    </Placemark>
  </Document>
</kml>"""

    from unittest.mock import patch
    from app.queue.producer import StreamProducer
    from app.api.controllers.geospatial_file_measurement_controller import measurement_service
    from pathlib import Path

    try:
        with patch.object(StreamProducer, "publish_job", return_value="1234-0"):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                files = {"file": ("test_features.kml", kml_content.encode("utf-8"), "application/vnd.google-earth.kml+xml")}
                resp = await client.post("/api/files/", files=files)
                assert resp.status_code == 201
                data = resp.json()
                assert data["filename"] == "test_features.kml"
                assert data["status"] in ("processing", "PROCESSING")
                file_id = data["id"]

                staged_files = list(Path("uploads").glob(f"{file_id}.*"))
                assert len(staged_files) == 1
                await measurement_service.process_staged_file(
                    file_id=file_id,
                    filename="test_features.kml",
                    file_size=len(kml_content),
                    file_path=staged_files[0]
                )

                meas_resp = await client.get(f"/api/files/{file_id}/measurements")
                assert meas_resp.status_code == 200
                meas_data = meas_resp.json()
                assert meas_data["total"] == 2

                poly_item = next(item for item in meas_data["items"] if item["geometry_type"] == "Polygon")
                assert poly_item["validation_status"] == "VALID"
                assert poly_item["measurement_method"] == "GEODESIC_WGS84"
                assert poly_item["area_sq_m"] > 1000000.0  
                assert poly_item["perimeter_m"] > 4000.0

                line_item = next(item for item in meas_data["items"] if item["geometry_type"] == "LineString")
                assert line_item["validation_status"] == "VALID"
                assert line_item["measurement_method"] == "GEODESIC_WGS84"
                assert line_item["length_m"] > 1100.0  
    finally:
        from app.db.database import engine
        await engine.dispose()  
