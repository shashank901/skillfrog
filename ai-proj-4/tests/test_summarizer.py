from __future__ import annotations

from backend.config import Settings
from backend.schemas import IssuePayload
from backend.summarizer import ReportSummarizer


def test_summarizer_fallback():
    settings = Settings(use_fake_llm=True, openai_api_key=None)
    summarizer = ReportSummarizer(settings)
    issues = [
        IssuePayload(
            issue_type="missing_values",
            severity="high",
            description="Missing rate high",
            recommendation="Impute",
        )
    ]
    summary = summarizer.summarize("dataset", issues, 0.2, 0.0)
    assert "dataset" in summary.lower()
    assert "missing" in summary.lower()
