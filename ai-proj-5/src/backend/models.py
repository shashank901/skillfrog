from datetime import datetime
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel


class ResearchReport(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    topic: str
    summary_md: str
    insights_json: str
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    sources: List["Source"] = Relationship(back_populates="report")


class Source(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    report_id: int = Field(foreign_key="researchreport.id")
    title: str
    url: str
    snippet: str

    report: Optional[ResearchReport] = Relationship(back_populates="sources")
