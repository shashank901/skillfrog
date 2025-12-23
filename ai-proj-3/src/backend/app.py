from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict

from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import Settings, load_settings
from .pipeline import RAGPipeline
from .schemas import ChatRequest, ChatResponse, HistoryResponse, IngestRequest, SourceCitation

LOGGER = logging.getLogger(__name__)
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


def create_app(settings: Settings | None = None) -> FastAPI:
    """Factory for FastAPI application."""
    settings = settings or load_settings()
    pipeline = RAGPipeline(settings=settings)

    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description="Customer support RAG agent for telecom FAQs.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin] if settings.frontend_origin != "*" else ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if FRONTEND_DIR.exists():
        app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
    else:  # pragma: no cover - present in repo
        LOGGER.warning("Frontend directory %s missing.", FRONTEND_DIR)

    app.state.settings = settings
    app.state.pipeline = pipeline

    @app.get("/health", tags=["system"])
    async def health() -> Dict[str, str]:
        return {"status": "ok", "environment": settings.environment}

    @app.get("/", response_class=FileResponse, include_in_schema=False)
    async def index() -> FileResponse:
        index_file = FRONTEND_DIR / "index.html"
        if not index_file.exists():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Frontend not found")
        return FileResponse(index_file)

    @app.get("/config", tags=["system"])
    async def read_config() -> Dict[str, Any]:
        cfg = settings.__dict__.copy()
        cfg.pop("openai_api_key", None)
        cfg.pop("gemini_api_key", None)
        return cfg

    @app.post("/ingest", response_model=Dict[str, Any], tags=["ingestion"])
    async def ingest_documents(payload: IngestRequest, pipeline: RAGPipeline = Depends(_get_pipeline)) -> Dict[str, Any]:
        try:
            metrics = pipeline.ingest(Path(payload.source_dir) if payload.source_dir else None)
            return {"status": "completed", "metrics": metrics}
        except FileNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    @app.post("/chat", response_model=ChatResponse, tags=["chat"])
    async def chat_endpoint(payload: ChatRequest, pipeline: RAGPipeline = Depends(_get_pipeline)) -> ChatResponse:
        try:
            result = pipeline.query(payload.question)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
        return ChatResponse(
            question=result["question"],
            answer=result["answer"],
            sources=[SourceCitation(**src) for src in result["sources"]],
        )

    @app.get("/history", response_model=HistoryResponse, tags=["chat"])
    async def history(
        limit: int = Query(default=10, ge=1, le=settings.chat_history_limit),
        pipeline: RAGPipeline = Depends(_get_pipeline),
    ) -> HistoryResponse:
        items = pipeline.history(limit)
        return HistoryResponse(
            items=[
                ChatResponse(
                    question=entry["question"],
                    answer=entry["answer"],
                    sources=[SourceCitation(**src) for src in entry["sources"]],
                )
                for entry in items
            ]
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        LOGGER.exception("Unhandled error while processing %s: %s", request.url, exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )

    return app


def _get_pipeline(request: Request) -> RAGPipeline:
    pipeline = getattr(request.app.state, "pipeline", None)
    if pipeline is None:  # pragma: no cover - defensive path
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Pipeline not initialized")
    return pipeline
