from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class DatasetRequest(BaseModel):
    dataset_name: Optional[str] = Field(default=None, description="Human readable dataset name")
    data_path: Optional[str] = Field(default=None, description="Relative path to dataset on server")
    records: Optional[List[Dict[str, object]]] = Field(default=None, description="Inline dataset as list of records")
    fmt: str = Field(default="csv", description="Dataset format: csv or json")


class IssuePayload(BaseModel):
    issue_type: str
    severity: str
    description: str
    recommendation: str
    affected_columns: Optional[List[str]] = None


class ValidationResponse(BaseModel):
    report_id: int
    dataset_name: str
    total_rows: int
    missing_rate: float
    duplicate_count: int
    outlier_rate: float
    issues: List[IssuePayload]
    summary: str
    created_at: datetime


class ReportSummary(BaseModel):
    id: int
    dataset_name: str
    total_rows: int
    missing_rate: float
    outlier_rate: float
    created_at: datetime


class PaginatedReports(BaseModel):
    items: List[ReportSummary]
    total: int


class HealthResponse(BaseModel):
    status: str
    environment: str
