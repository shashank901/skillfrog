from __future__ import annotations

from backend.config import Settings
from backend.reviewers import ReviewPipeline


def test_pipeline_with_fake_llm(sample_code):
    settings = Settings(use_fake_llm=True, openai_api_key=None)
    pipeline = ReviewPipeline(settings)
    result = pipeline.review(sample_code, "unit test")
    assert result.summary
    assert result.issues


def test_pipeline_limits_issues(sample_code):
    settings = Settings(use_fake_llm=True, openai_api_key=None, max_issues=1)
    pipeline = ReviewPipeline(settings)
    result = pipeline.review(sample_code + "\n" + "a = [1]*150", "test")
    assert len(result.issues) <= 1
