from __future__ import annotations

from typing import Iterable, List

from .schemas import IssuePayload


def serialize_issue(issue: IssuePayload) -> dict:
    return {
        "issue_type": issue.issue_type,
        "severity": issue.severity,
        "description": issue.description,
        "recommendation": issue.recommendation,
        "affected_columns": issue.affected_columns or [],
    }


def serialize_issues(issues: Iterable[IssuePayload]) -> List[dict]:
    return [serialize_issue(issue) for issue in issues]
