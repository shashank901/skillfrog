from __future__ import annotations

import logging
from typing import List

from .config import Settings
from .schemas import IssuePayload

LOGGER = logging.getLogger(__name__)

try:
    from langchain_openai import ChatOpenAI
except ImportError:  # pragma: no cover
    ChatOpenAI = None  # type: ignore


class ReportSummarizer:
    """Generates narrative summary for validation results."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.llm = None
        if not settings.use_fake_llm and settings.openai_api_key and ChatOpenAI:
            self.llm = ChatOpenAI(model=settings.model_name, temperature=0, api_key=settings.openai_api_key)

    def summarize(self, dataset_name: str, issues: List[IssuePayload], missing_rate: float, outlier_rate: float) -> str:
        if self.llm is None:
            return self._fallback_summary(dataset_name, issues, missing_rate, outlier_rate)
        prompt = (
            "You are a data quality analyst. Summarize the validation results using concise language. "
            "Include key metrics (missing rate, duplicates, outliers) and highlight top remediation steps."
        )
        detail = (
            f"Dataset: {dataset_name}\nMissing Rate: {missing_rate:.2%}\n"
            f"Outlier Rate: {outlier_rate:.2%}\nIssues: {', '.join(issue.issue_type for issue in issues) or 'None'}"
        )
        try:
            response = self.llm.invoke(prompt + "\n\n" + detail)
            if hasattr(response, "content"):
                return response.content.strip()
        except Exception as exc:  # pragma: no cover
            LOGGER.exception("LLM summarization failed: %s", exc)
        return self._fallback_summary(dataset_name, issues, missing_rate, outlier_rate)

    def _fallback_summary(self, dataset_name: str, issues: List[IssuePayload], missing_rate: float, outlier_rate: float) -> str:
        if not issues:
            return (
                f"Dataset '{dataset_name}' passes core quality checks. Missing rate {missing_rate:.2%} and outlier rate {outlier_rate:.2%}."
            )
        top_issue = issues[0]
        return (
            f"Dataset '{dataset_name}' requires attention: top issue '{top_issue.issue_type}' ({top_issue.severity}). "
            f"Missing rate {missing_rate:.2%}, outlier rate {outlier_rate:.2%}. Prioritize remediation steps such as {top_issue.recommendation}."
        )
