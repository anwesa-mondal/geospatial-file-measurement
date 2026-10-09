from fastapi import FastAPI
from app.api.controllers import readiness_controller

app = FastAPI(
    title="Geospatial File Measurement API",
    version="1.0.0",
    description="API for ingesting geospatial files (Shapefile, KML) and calculating geometry measurements.",
)

app.include_router(readiness_controller.router)