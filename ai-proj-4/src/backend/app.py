from __future__ import annotations

import logging
from typing import Iterator, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlmodel import Session

from .config import Settings, load_settings
from .db import Database
from .schemas import DatasetRequest, HealthResponse, PaginatedReports, ValidationResponse
from .services import ValidationService

LOGGER = logging.getLogger(__name__)


def create_app(settings: Optional[Settings] = None) -> FastAPI:
    settings = settings or load_settings()
    database = Database(settings)
    database.create_schema()

    app = FastAPI(title=settings.app_name, description="AI Data Quality Validation Agent", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.settings = settings
    app.state.database = database

    @app.get("/health", response_model=HealthResponse, tags=["system"])
    async def health() -> HealthResponse:
        return HealthResponse(status="ok", environment=settings.environment)

    @app.post("/validate", response_model=ValidationResponse, tags=["validation"])
    async def validate_dataset(
        payload: DatasetRequest,
        service: ValidationService = Depends(get_service),
    ) -> ValidationResponse:
        try:
            return service.validate_dataset(payload)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    @app.get("/reports", response_model=PaginatedReports, tags=["validation"])
    async def list_reports(
        dataset_name: Optional[str] = Query(default=None),
        limit: int = Query(default=10, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
        service: ValidationService = Depends(get_service),
    ) -> PaginatedReports:
        return service.list_reports(dataset_name, limit, offset)

    @app.get("/reports/{report_id}", response_model=ValidationResponse, tags=["validation"])
    async def get_report(report_id: int, service: ValidationService = Depends(get_service)) -> ValidationResponse:
        try:
            return service.get_report(report_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    @app.exception_handler(Exception)
    async def handle_exception(_: Request, exc: Exception):
        LOGGER.exception("Unhandled exception: %s", exc)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    return app


def get_settings(request: Request) -> Settings:
    settings = getattr(request.app.state, "settings", None)
    if settings is None:  # pragma: no cover
        raise RuntimeError("Settings not initialized")
    return settings


def get_database(request: Request) -> Database:
    database = getattr(request.app.state, "database", None)
    if database is None:  # pragma: no cover
        raise RuntimeError("Database not initialized")
    return database


def get_session(request: Request) -> Iterator[Session]:
    database = get_database(request)
    with database.session() as session:
        yield session


def get_service(
    settings: Settings = Depends(get_settings),
    session: Session = Depends(get_session),
) -> ValidationService:
    return ValidationService(settings=settings, session=session)
