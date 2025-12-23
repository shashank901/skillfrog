from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session

from .agent import FinanceAdvisorAgent
from .config import Settings, load_settings
from .db import Database
from .ingestion import ingest_from_path
from .schemas import (
    ConversationResponse,
    HistoryResponse,
    IngestRequest,
    RecommendationRequest,
    RecommendationResponse,
    UserResponse,
)
from .services import FinanceService

LOGGER = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()
    database = Database(settings=settings)
    database.create_schema()

    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description="AI Personal Finance Advisor Agent API",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin] if settings.frontend_origin != "*" else ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.settings = settings
    app.state.database = database

    @app.get("/health", tags=["system"])
    async def health() -> Dict[str, str]:
        return {"status": "ok", "environment": settings.environment}

    @app.post("/ingest", tags=["data"], response_model=Dict[str, Any])
    async def ingest_data(
        request: IngestRequest, service: FinanceService = Depends(get_service)
    ) -> Dict[str, Any]:
        try:
            csv_path: Optional[Path]
            if request.path:
                csv_path = Path(request.path)
                if not csv_path.is_absolute():
                    csv_path = settings.data_dir / csv_path
            else:
                csv_path = None
            metrics = ingest_from_path(settings, service.session, csv_path)
            return {"status": "completed", "metrics": metrics}
        except FileNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    @app.get("/users", tags=["data"], response_model=List[UserResponse])
    async def list_users(service: FinanceService = Depends(get_service)) -> List[UserResponse]:
        users = service.get_users()
        return [
            UserResponse(id=user.id, name=user.name, income_monthly=user.income_monthly, risk_tolerance=user.risk_tolerance)
            for user in users
        ]

    @app.post("/recommend", tags=["advisor"], response_model=RecommendationResponse)
    async def recommend(
        payload: RecommendationRequest,
        advisor: FinanceAdvisorAgent = Depends(get_advisor),
    ) -> RecommendationResponse:
        try:
            result = advisor.recommend(payload.user_id, payload.question or "")
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        return RecommendationResponse(
            user_id=payload.user_id,
            question=payload.question or "",
            summary=result.summary,
            recommended_actions=result.recommended_actions,
            investment_split=result.investment_split,
            savings_rate=result.savings_rate,
            monthly_projection=result.monthly_projection,
        )

    @app.get("/history/{user_id}", tags=["advisor"], response_model=HistoryResponse)
    async def history(user_id: int, service: FinanceService = Depends(get_service)) -> HistoryResponse:
        try:
            items = service.get_recent_conversations(user_id, limit=settings.memory_window)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        return HistoryResponse(
            items=[
                ConversationResponse(
                    id=conv.id,
                    user_id=conv.user_id,
                    question=conv.question,
                    answer=conv.answer,
                    created_at=conv.created_at,
                )
                for conv in items
            ]
        )

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        LOGGER.debug("%s %s", request.method, request.url.path)
        response: Response = await call_next(request)
        return response

    return app


def get_database(request: Request) -> Database:
    database = getattr(request.app.state, "database", None)
    if database is None:  # pragma: no cover
        raise RuntimeError("Database not initialized")
    return database


def get_settings(request: Request) -> Settings:
    settings: Optional[Settings] = getattr(request.app.state, "settings", None)
    if settings is None:  # pragma: no cover
        raise RuntimeError("Settings not initialized")
    return settings


def get_session(request: Request) -> Iterator[Session]:
    database = get_database(request)
    with database.session() as session:
        yield session


def get_service(session: Session = Depends(get_session)) -> FinanceService:
    return FinanceService(session=session)


def get_advisor(
    settings: Settings = Depends(get_settings),
    service: FinanceService = Depends(get_service),
) -> FinanceAdvisorAgent:
    return FinanceAdvisorAgent(settings=settings, service=service)
