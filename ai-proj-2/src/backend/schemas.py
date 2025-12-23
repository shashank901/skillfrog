from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ReviewRequest(BaseModel):
    code: Optional[str] = Field(default=None, description="Raw Python source code")
    repository: Optional[str] = Field(default=None, description="GitHub repo e.g. org/repo")
    commit_sha: Optional[str] = Field(default=None)
    file_path: Optional[str] = Field(default=None)
    language: str = Field(default="python")


class IssuePayload(BaseModel):
    severity: str
    issue_type: str
    description: str
    suggestion: str
    line_start: Optional[int] = None
    line_end: Optional[int] = None


class ReviewResponse(BaseModel):
    id: int
    summary: str
    issues: List[IssuePayload]
    created_at: datetime


class ReviewSummary(BaseModel):
    id: int
    repository: Optional[str]
    commit_sha: Optional[str]
    file_path: Optional[str]
    summary: str
    created_at: datetime
    issue_count: int


class PaginatedReviews(BaseModel):
    items: List[ReviewSummary]
    total: int


class HealthResponse(BaseModel):
    status: str
    environment: str
