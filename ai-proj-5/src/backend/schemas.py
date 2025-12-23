from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ResearchRequest(BaseModel):
    topic: str = Field(..., min_length=3, description="Research topic or question")
    max_sources: Optional[int] = Field(default=None, ge=1, le=15)


class PlannerStep(BaseModel):
    step: str
    subtopic: str


class SourcePayload(BaseModel):
    title: str
    url: str
    snippet: str


class Insight(BaseModel):
    heading: str
    content: str


class ResearchResponse(BaseModel):
    report_id: int
    topic: str
    summary_md: str
    insights: List[Insight]
    sources: List[SourcePayload]
    planner_steps: List[PlannerStep]
    created_at: datetime


class ReportSummary(BaseModel):
    id: int
    topic: str
    created_at: datetime


class PaginatedReports(BaseModel):
    items: List[ReportSummary]
    total: int


class HealthResponse(BaseModel):
    status: str
    environment: str
