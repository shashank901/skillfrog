from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    path: Optional[str] = Field(
        default=None, description="Optional CSV path; defaults to sample data directory."
    )


class UserResponse(BaseModel):
    id: int
    name: str
    income_monthly: float
    risk_tolerance: str


class RecommendationRequest(BaseModel):
    user_id: int = Field(..., ge=1)
    question: Optional[str] = Field(
        default="What is my monthly savings potential?",
        description="Optional user question to guide the advisor.",
    )


class RecommendationResponse(BaseModel):
    user_id: int
    question: str
    summary: str
    recommended_actions: List[str]
    investment_split: List[str]
    savings_rate: float
    monthly_projection: float


class ConversationResponse(BaseModel):
    id: int
    user_id: int
    question: str
    answer: str
    created_at: datetime


class HistoryResponse(BaseModel):
    items: List[ConversationResponse]
