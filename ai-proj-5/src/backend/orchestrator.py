from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List

from .agents import PlannerAgent, ResearcherAgent, SummarizerAgent
from .config import Settings

LOGGER = logging.getLogger(__name__)


class ResearchOrchestrator:
    """Coordinates planner, researcher, and summarizer agents."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.planner = PlannerAgent(settings)
        self.researcher = ResearcherAgent(settings)
        self.summarizer = SummarizerAgent(settings)
        self.cached_data = self._load_cache(settings.data_cache_path)

    def _load_cache(self, path: Path) -> Dict[str, List[Dict[str, str]]]:
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                cache = {}
                for entry in data.get("queries", []):
                    cache[entry["query"].lower()] = entry.get("results", [])
                return cache
            except json.JSONDecodeError:  # pragma: no cover
                LOGGER.warning("Invalid cache file, ignoring")
        return {}

    def run(self, topic: str, max_sources: int | None = None) -> Dict[str, object]:
        max_sources = max_sources or self.settings.default_max_sources
        planner_steps = self.planner.plan(topic)

        evidence: List[Dict[str, str]] = []
        sources: List[Dict[str, str]] = []
        for step in planner_steps:
            query_results = self._search_with_fallback(step)
            for item in query_results[:max_sources]:
                evidence.append(item)
                sources.append(item)

        summary_payload = self.summarizer.summarize(topic, evidence)
        insights = [
            {"heading": insight.get("heading", "Insight"), "content": insight.get("content", "")} 
            for insight in summary_payload.get("insights", [])
        ] or [
            {"heading": "Preliminary Insight", "content": f"Review collected evidence on {topic} for deeper analysis."}
        ]
        return {
            "planner_steps": [{"step": step, "subtopic": step} for step in planner_steps],
            "summary_md": summary_payload.get("summary", ""),
            "insights": insights,
            "sources": sources,
        }

    def _search_with_fallback(self, query: str) -> List[Dict[str, str]]:
        results = self.researcher.search(query)
        if results:
            return results
        cached = self.cached_data.get(query.lower())
        if cached:
            LOGGER.info("Falling back to cached evidence for query '%s'", query)
            return cached
        if self.cached_data:
            LOGGER.info("Using general cache fallback for query '%s'", query)
            return next(iter(self.cached_data.values()))
        return []
