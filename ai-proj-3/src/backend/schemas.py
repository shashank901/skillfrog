from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    """Request body for ingestion endpoint."""

    source_dir: Optional[str] = Field(
        default=None,
        description="Optional override directory containing PDF or text documents.",
    )


class SourceCitation(BaseModel):
    """Metadata for a retrieved document chunk."""

    rank: int = Field(..., description="Ranked order from the similarity search.")
    file: str = Field(..., description="Human-readable file name for the chunk.")
    page: str = Field(..., description="Page number or n/a if not available.")
    chunk_id: Optional[str] = Field(default="", description="Chunk identifier in the store.")
    source: Optional[str] = Field(default="", description="Absolute source path.")


class ChatRequest(BaseModel):
    """Chat endpoint payload."""

    question: str = Field(..., min_length=1, description="Question to ask the support agent.")


class ChatResponse(BaseModel):
    """Standard chat response payload."""

    question: str
    answer: str
    sources: List[SourceCitation]


class HistoryResponse(BaseModel):
    """List of previous messages for UI replay."""

    items: List[ChatResponse]
