from datetime import datetime
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel


class ValidationReport(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    dataset_name: str
    total_rows: int
    missing_rate: float
    duplicate_count: int
    outlier_rate: float
    summary: str
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    issues: List["Issue"] = Relationship(back_populates="report")


class Issue(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    report_id: int = Field(foreign_key="validationreport.id")
    issue_type: str
    severity: str
    description: str
    recommendation: str
    affected_columns: Optional[str] = None

    report: Optional["ValidationReport"] = Relationship(back_populates="issues")
