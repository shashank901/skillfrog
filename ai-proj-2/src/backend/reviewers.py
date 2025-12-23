
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import List

from .config import Settings
from .schemas import IssuePayload
from .utils import deduplicate_issues, severity_to_numeric

LOGGER = logging.getLogger(__name__)

try:
    from langchain_openai import ChatOpenAI
except ImportError:  # pragma: no cover
    ChatOpenAI = None  # type: ignore


@dataclass
class ReviewResult:
    summary: str
    issues: List[IssuePayload]


class HeuristicReviewer:
    """Performs lightweight static checks on Python code."""

    @staticmethod
    def analyze(code: str) -> List[IssuePayload]:
        issues: List[IssuePayload] = []
        lines = code.splitlines()
        for idx, line in enumerate(lines, start=1):
            if len(line) > 120:
                issues.append(
                    IssuePayload(
                        severity="low",
                        issue_type="style",
                        description=f"Line {idx} exceeds 120 characters.",
                        suggestion="Break the line or refactor into helper functions.",
                        line_start=idx,
                        line_end=idx,
                    )
                )
            if line.rstrip().endswith("print("):
                issues.append(
                    IssuePayload(
                        severity="medium",
                        issue_type="logic",
                        description=f"Suspicious print statement at line {idx}.",
                        suggestion="Check parentheses balance; looks like unfinished call.",
                        line_start=idx,
                        line_end=idx,
                    )
                )
        if "for key in dict.keys():" in code:
            issues.append(
                IssuePayload(
                    severity="medium",
                    issue_type="performance",
                    description="Using dict.keys() inside loop is inefficient.",
                    suggestion="Iterate directly over the dictionary: for key in dict:",
                )
            )
        return issues


class LLMReviewer:
    """LangChain-powered reviewer that produces rich feedback."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.llm = None
        if not settings.use_fake_llm and settings.openai_api_key and ChatOpenAI:
            self.llm = ChatOpenAI(model=settings.model_name, temperature=0, api_key=settings.openai_api_key)

    def analyze(self, code: str, context: str) -> ReviewResult:
        if not code:
            raise ValueError("Code payload is empty")

        if self.llm is None:
            summary = (
                "Static analysis indicates opportunities to improve readability and performance. "
                "Consider adding docstrings and handling edge cases explicitly."
            )
            issues = [
                IssuePayload(
                    severity="medium",
                    issue_type="documentation",
                    description="Function lacks docstring.",
                    suggestion="Add docstring summarizing parameters and return values.",
                )
            ]
            return ReviewResult(summary=summary, issues=issues)

        prompt = (
            "You are an expert Python code reviewer. Analyze the provided code and highlight issues in logic, "
            "performance, and style. Respond in JSON with fields: issues (list with severity, issue_type, description, "
            "suggestion, line_start, line_end) and summary. Consider context: "
            f"{context or 'N/A'}.\n\n"
            "Code:\n"
            f"{code}\n"
        )
        try:
            response = self.llm.invoke(prompt)
            if hasattr(response, "content"):
                data = json.loads(response.content)
                issues = [IssuePayload(**issue) for issue in data.get("issues", [])]
                return ReviewResult(summary=data.get("summary", ""), issues=issues)
        except Exception as exc:  # pragma: no cover
            LOGGER.exception("LLM review failed: %s", exc)
        return ReviewResult(summary="LLM review unavailable.", issues=[])


class ReviewPipeline:
    """Combines heuristics and LLM reviewer into consolidated result."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.heuristic = HeuristicReviewer()
        self.llm_reviewer = LLMReviewer(settings)

    def review(self, code: str, context: str) -> ReviewResult:
        issues = self.heuristic.analyze(code)
        llm_result = self.llm_reviewer.analyze(code, context)
        combined = issues + llm_result.issues
        combined.sort(key=lambda issue: severity_to_numeric(issue.severity), reverse=True)
        trimmed = combined[: self.settings.max_issues]
        unique = deduplicate_issues(trimmed)
        summary = llm_result.summary or "Automated review completed with heuristic checks."
        return ReviewResult(summary=summary, issues=unique)
