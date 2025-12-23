from __future__ import annotations

from backend.agents import PlannerAgent, SummarizerAgent
from backend.config import Settings


def test_planner_returns_steps(tmp_path):
    settings = Settings(use_fake_llm=True)
    planner = PlannerAgent(settings)
    steps = planner.plan("climate change impact")
    assert len(steps) >= 3


def test_summarizer_fallback(tmp_path):
    settings = Settings(use_fake_llm=True)
    summarizer = SummarizerAgent(settings)
    payload = summarizer.summarize("AI in healthcare", [
        {"title": "Source", "snippet": "Evidence"}
    ])
    assert "summary" in payload
    assert payload["insights"]
