from __future__ import annotations

import pytest

from src.backend.pipeline import RAGPipeline


def test_pipeline_ingest_collects_metrics(pipeline: RAGPipeline, test_settings):
    metrics = pipeline.ingest(test_settings.docs_path)
    assert metrics["files"] >= 2
    assert metrics["chunks"] > 0


def test_pipeline_query_returns_answer(pipeline: RAGPipeline):
    result = pipeline.query("How do I enable international roaming?")
    assert "roaming" in result["answer"].lower()
    assert result["sources"], "Expected citations to be returned"


def test_pipeline_empty_question_invalid(pipeline: RAGPipeline):
    with pytest.raises(ValueError):
        pipeline.query("   ")
