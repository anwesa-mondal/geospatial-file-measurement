from contextlib import asynccontextmanager
from fastapi import FastAPI
import logging

from dotenv import load_dotenv
load_dotenv()

from app.api.controllers import geospatial_file_measurement_controller
from app.db.database import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    
    await init_db()
    logger.info("Database schemas initialized.")
    yield

app = FastAPI(
    title="Geospatial File Measurement API",
    version="1.0.0",
    description="API for ingesting geospatial files (Shapefile, KML) and calculating geometry measurements.",
    lifespan=lifespan,
)

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}

app.include_router(geospatial_file_measurement_controller.router, prefix="/api/files", tags=["Files"])

import os
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"

if frontend_dist.exists():
    assets_dir = frontend_dist / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        file_path = frontend_dist / full_path
        if full_path and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(frontend_dist / "index.html")