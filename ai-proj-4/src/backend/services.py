from __future__ import annotations

import logging
from typing import List, Optional

import pandas as pd
from sqlmodel import Session, select

from .config import Settings
from .models import Issue, ValidationReport
from .schemas import DatasetRequest, IssuePayload, PaginatedReports, ReportSummary, ValidationResponse
from .summarizer import ReportSummarizer
from .validators import DataValidator, ValidationResult
from .utils import serialize_issue

LOGGER = logging.getLogger(__name__)


class ValidationService:
    """Coordinates dataset loading, validation, summarization, and persistence."""

    def __init__(self, settings: Settings, session: Session):
        self.settings = settings
        self.session = session
        self.validator = DataValidator(settings)
        self.summarizer = ReportSummarizer(settings)

    def validate_dataset(self, payload: DatasetRequest) -> ValidationResponse:
        df, dataset_name = self._load_dataset(payload)
        result = self.validator.validate(df, dataset_name)
        summary_text = self.summarizer.summarize(
            dataset_name=result.dataset_name,
            issues=result.issues,
            missing_rate=result.missing_rate,
            outlier_rate=result.outlier_rate,
        )
        report = ValidationReport(
            dataset_name=result.dataset_name,
            total_rows=result.total_rows,
            missing_rate=result.missing_rate,
            duplicate_count=result.duplicate_count,
            outlier_rate=result.outlier_rate,
            summary=summary_text,
        )
        self.session.add(report)
        self.session.flush()

        issue_models: List[Issue] = []
        for issue in result.issues:
            issue_models.append(
                Issue(
                    report_id=report.id,
                    issue_type=issue.issue_type,
                    severity=issue.severity,
                    description=issue.description,
                    recommendation=issue.recommendation,
                    affected_columns=",".join(issue.affected_columns or []),
                )
            )
        self.session.add_all(issue_models)
        self.session.commit()

        return ValidationResponse(
            report_id=report.id,
            dataset_name=report.dataset_name,
            total_rows=report.total_rows,
            missing_rate=report.missing_rate,
            duplicate_count=report.duplicate_count,
            outlier_rate=report.outlier_rate,
            issues=[IssuePayload(**serialize_issue(issue)) for issue in result.issues],
            summary=report.summary,
            created_at=report.created_at,
        )

    def list_reports(self, dataset_name: Optional[str], limit: int, offset: int) -> PaginatedReports:
        query = select(ValidationReport).order_by(ValidationReport.created_at.desc())
        if dataset_name:
            query = query.where(ValidationReport.dataset_name == dataset_name)
        items = self.session.exec(query.offset(offset).limit(limit)).all()
        total_query = select(ValidationReport)
        if dataset_name:
            total_query = total_query.where(ValidationReport.dataset_name == dataset_name)
        total = len(self.session.exec(total_query).all())
        summaries = [
            ReportSummary(
                id=item.id,
                dataset_name=item.dataset_name,
                total_rows=item.total_rows,
                missing_rate=item.missing_rate,
                outlier_rate=item.outlier_rate,
                created_at=item.created_at,
            )
            for item in items
        ]
        return PaginatedReports(items=summaries, total=total)

    def get_report(self, report_id: int) -> ValidationResponse:
        report = self.session.get(ValidationReport, report_id)
        if not report:
            raise ValueError(f"Report {report_id} not found")
        issues = self.session.exec(select(Issue).where(Issue.report_id == report_id)).all()
        payloads = [
            IssuePayload(
                issue_type=issue.issue_type,
                severity=issue.severity,
                description=issue.description,
                recommendation=issue.recommendation,
                affected_columns=issue.affected_columns.split(",") if issue.affected_columns else [],
            )
            for issue in issues
        ]
        return ValidationResponse(
            report_id=report.id,
            dataset_name=report.dataset_name,
            total_rows=report.total_rows,
            missing_rate=report.missing_rate,
            duplicate_count=report.duplicate_count,
            outlier_rate=report.outlier_rate,
            issues=payloads,
            summary=report.summary,
            created_at=report.created_at,
        )

    def _load_dataset(self, payload: DatasetRequest) -> tuple[pd.DataFrame, str]:
        from .validators import load_dataset

        return load_dataset(self.settings, payload)
