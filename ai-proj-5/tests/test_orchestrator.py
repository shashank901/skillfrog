from __future__ import annotations

import json
from pathlib import Path

from backend.config import Settings
from backend.orchestrator import ResearchOrchestrator


def test_orchestrator_uses_cache(tmp_path):
    cache = tmp_path / "cache.json"
    cache.write_text(
        json.dumps(
            {
                "queries": [
                    {
                        "query": "Define key concepts of testing",
                        "results": [
                            {
                                "title": "Test Source",
                                "url": "https://example.com",
                                "snippet": "Sample evidence",
                            }
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    settings = Settings(use_fake_llm=True, use_fake_search=True, data_cache_path=cache)
    orchestrator = ResearchOrchestrator(settings)
    result = orchestrator.run("testing")
    assert result["sources"], "Should leverage cached data for fake search"
    assert "summary_md" in result
