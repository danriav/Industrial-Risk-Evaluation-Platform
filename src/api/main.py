from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy.exc import SQLAlchemyError
from starlette.responses import Response

from .config import settings
from .errors import sqlalchemy_error_handler
from .routers import assets, catalog, discrepancies, maintenance, predictions, sensors
from .schemas import HealthResponse


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="API Core para MERO, motor de evaluacion de riesgo industrial.",
    )
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_error_handler)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    if settings.force_https:
        app.add_middleware(HTTPSRedirectMiddleware)

    app.include_router(assets.router, prefix="/api/v1", tags=["assets"])
    app.include_router(catalog.router, prefix="/api/v1", tags=["failure-catalog"])
    app.include_router(sensors.router, prefix="/api/v1", tags=["sensor-observations"])
    app.include_router(maintenance.router, prefix="/api/v1", tags=["maintenance"])
    app.include_router(discrepancies.router, prefix="/api/v1", tags=["discrepancies"])
    app.include_router(predictions.router, prefix="/api/v1", tags=["predictions"])

    @app.get("/health", response_model=HealthResponse, tags=["platform"])
    def health() -> HealthResponse:
        return HealthResponse(status="ok", service="mero-api")

    @app.get("/metrics", include_in_schema=False)
    def metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return app


app = create_app()
