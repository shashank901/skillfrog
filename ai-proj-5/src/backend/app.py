from __future__ import annotations

import logging
from typing import Iterator

from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlmodel import Session

from .config import Settings, load_settings
from .db import Database
from .schemas import HealthResponse, PaginatedReports, ResearchRequest, ResearchResponse, ReportSummary
from .services import ResearchService

LOGGER = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()
    database = Database(settings)
    database.create_schema()

    app = FastAPI(title=settings.app_name, version="1.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.state.settings = settings
    app.state.database = database

    @app.get("/health", response_model=HealthResponse, tags=["system"])
    async def health() -> HealthResponse:
        return HealthResponse(status="ok", environment=settings.environment)

    @app.post("/research", response_model=ResearchResponse, tags=["research"])
    async def run_research(payload: ResearchRequest, service: ResearchService = Depends(get_service)) -> ResearchResponse:
        try:
            return service.run_research(payload)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    @app.get("/reports", response_model=PaginatedReports, tags=["research"])
    async def list_reports(
        limit: int = Query(default=10, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
        service: ResearchService = Depends(get_service),
    ) -> PaginatedReports:
        reports = service.list_reports(limit=limit, offset=offset)
        total = service.count_reports()
        items = [ReportSummary(id=report.id, topic=report.topic, created_at=report.created_at) for report in reports]
        return PaginatedReports(items=items, total=total)

    @app.get("/reports/{report_id}", response_model=ResearchResponse, tags=["research"])
    async def get_report(report_id: int, service: ResearchService = Depends(get_service)) -> ResearchResponse:
        try:
            return service.get_report(report_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_: Request, exc: Exception):  # pragma: no cover
        LOGGER.exception("Unhandled exception: %s", exc)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    return app


def get_settings(request: Request) -> Settings:
    settings = getattr(request.app.state, "settings", None)
    if settings is None:  # pragma: no cover
        raise RuntimeError("Settings not initialised")
    return settings


def get_database(request: Request) -> Database:
    database = getattr(request.app.state, "database", None)
    if database is None:  # pragma: no cover
        raise RuntimeError("Database not initialised")
    return database


def get_session(request: Request) -> Iterator[Session]:
    database = get_database(request)
    with database.session() as session:
        yield session


def get_service(settings: Settings = Depends(get_settings), session: Session = Depends(get_session)) -> ResearchService:
    return ResearchService(settings=settings, session=session)
