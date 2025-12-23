from datetime import datetime
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel


class Review(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    repository: Optional[str] = Field(default=None)
    commit_sha: Optional[str] = Field(default=None)
    file_path: Optional[str] = Field(default=None)
    summary: str
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    issues: List["Issue"] = Relationship(back_populates="review")


class Issue(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    review_id: int = Field(foreign_key="review.id")
    severity: str
    issue_type: str
    description: str
    suggestion: str
    line_start: Optional[int] = None
    line_end: Optional[int] = None

    review: Optional["Review"] = Relationship(back_populates="issues")
