from __future__ import annotations

import logging
from typing import Iterable, List

from .schemas import IssuePayload

LOGGER = logging.getLogger(__name__)


def deduplicate_issues(issues: Iterable[IssuePayload]) -> List[IssuePayload]:
    """Remove duplicate issues by (description, suggestion)."""
    seen = set()
    unique: List[IssuePayload] = []
    for issue in issues:
        key = (issue.description.strip(), issue.suggestion.strip())
        if key in seen:
            continue
        seen.add(key)
        unique.append(issue)
    return unique


def severity_to_numeric(severity: str) -> int:
    mapping = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    return mapping.get(severity.lower(), 1)
