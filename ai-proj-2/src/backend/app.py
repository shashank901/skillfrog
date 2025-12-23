from __future__ import annotations

import logging
from typing import Any, Dict, Iterator, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlmodel import Session

from .config import Settings, load_settings
from .db import Database
from .models import Issue, Review
from .schemas import (
    HealthResponse,
    IssuePayload,
    PaginatedReviews,
    ReviewRequest,
    ReviewResponse,
    ReviewSummary,
)
from .services import ReviewService

LOGGER = logging.getLogger(__name__)


def create_app(settings: Optional[Settings] = None) -> FastAPI:
    settings = settings or load_settings()
    database = Database(settings)
    database.create_schema()

    app = FastAPI(title=settings.app_name, version="1.0.0", description="AI Code Reviewer Agent")

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

    @app.post("/review", response_model=ReviewResponse, tags=["reviews"])
    async def create_review(
        payload: ReviewRequest,
        service: ReviewService = Depends(get_service),
    ) -> ReviewResponse:
        try:
            return service.perform_review(payload)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    @app.get("/reviews", response_model=PaginatedReviews, tags=["reviews"])
    async def list_reviews(
        repo: Optional[str] = Query(default=None),
        limit: int = Query(default=10, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
        service: ReviewService = Depends(get_service),
    ) -> PaginatedReviews:
        items = service.list_reviews(repo, limit, offset)
        total = service.count_reviews(repo)
        summaries = [
            ReviewSummary(
                id=review.id,
                repository=review.repository,
                commit_sha=review.commit_sha,
                file_path=review.file_path,
                summary=review.summary,
                created_at=review.created_at,
                issue_count=len(review.issues),
            )
            for review in items
        ]
        return PaginatedReviews(items=summaries, total=total)

    @app.get("/reviews/{review_id}", response_model=ReviewResponse, tags=["reviews"])
    async def get_review(review_id: int, service: ReviewService = Depends(get_service)) -> ReviewResponse:
        try:
            review = service.get_review(review_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        issues = [
            IssuePayload(
                severity=issue.severity,
                issue_type=issue.issue_type,
                description=issue.description,
                suggestion=issue.suggestion,
                line_start=issue.line_start,
                line_end=issue.line_end,
            )
            for issue in review.issues
        ]
        return ReviewResponse(id=review.id, summary=review.summary, issues=issues, created_at=review.created_at)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        LOGGER.exception("Unhandled exception on %s: %s", request.url.path, exc)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    return app


def get_database(request: Request) -> Database:
    database = getattr(request.app.state, "database", None)
    if database is None:  # pragma: no cover
        raise RuntimeError("Database not initialized")
    return database


def get_settings(request: Request) -> Settings:
    settings = getattr(request.app.state, "settings", None)
    if settings is None:  # pragma: no cover
        raise RuntimeError("Settings not initialized")
    return settings


def get_session(request: Request) -> Iterator[Session]:
    database = get_database(request)
    with database.session() as session:
        yield session


def get_service(
    settings: Settings = Depends(get_settings),
    session: Session = Depends(get_session),
) -> ReviewService:
    return ReviewService(settings=settings, session=session)
