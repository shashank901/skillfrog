from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import List

import httpx

from .config import Settings

LOGGER = logging.getLogger(__name__)

try:
    from langchain.chat_models import ChatOpenAI
    from langchain.prompts import ChatPromptTemplate
except ImportError:  # pragma: no cover
    ChatOpenAI = None  # type: ignore
    ChatPromptTemplate = None  # type: ignore


@dataclass
class PlannerAgent:
    settings: Settings

    def plan(self, topic: str) -> List[str]:
        if self.settings.use_fake_llm or ChatOpenAI is None:
            LOGGER.info("Planner using fallback prompts")
            return [f"Define key concepts of {topic}", f"Identify recent developments about {topic}", f"Highlight challenges and opportunities in {topic}"]

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "You break research problems into concrete search queries."),
                ("human", "Topic: {topic}. Provide 3 distinct sub-questions."),
            ]
        )
        chain = prompt | ChatOpenAI(model=self.settings.model_name, temperature=0, api_key=self.settings.openai_api_key)
        response = chain.invoke({"topic": topic})
        content = response.content if hasattr(response, "content") else str(response)
        return [line.strip("- ") for line in content.splitlines() if line.strip()][:3]


@dataclass
class ResearcherAgent:
    settings: Settings

    def search(self, query: str) -> List[dict]:
        if self.settings.use_fake_search or not self.settings.serpapi_api_key:
            LOGGER.info("Researcher using cached results for query '%s'", query)
            return []
        params = {
            "engine": "google",
            "q": query,
            "num": 5,
            "api_key": self.settings.serpapi_api_key,
        }
        try:
            response = httpx.get("https://serpapi.com/search", params=params, timeout=15.0)
            response.raise_for_status()
            organic = response.json().get("organic_results", [])
            return [
                {
                    "title": item.get("title", "Untitled"),
                    "url": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                }
                for item in organic
            ]
        except httpx.HTTPError as exc:  # pragma: no cover
            LOGGER.exception("SerpAPI request failed: %s", exc)
            return []


@dataclass
class SummarizerAgent:
    settings: Settings

    def summarize(self, topic: str, evidence: List[dict]) -> dict:
        if self.settings.use_fake_llm or ChatOpenAI is None:
            insights = [
                {
                    "heading": "Key Findings",
                    "content": f"{topic} adoption is accelerating based on available sources."
                }
            ]
            summary = f"## {topic}\n\n- Generated summary placeholder using cached data."
            return {"summary": summary, "insights": insights}

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an analyst generating concise research summaries with bullet insights and source references.",
                ),
                (
                    "human",
                    "Topic: {topic}. Evidence: {evidence}. Produce Markdown summary and JSON insights list",
                ),
            ]
        )
        chain = prompt | ChatOpenAI(model=self.settings.model_name, temperature=0.3, api_key=self.settings.openai_api_key)
        response = chain.invoke({"topic": topic, "evidence": json.dumps(evidence)})
        content = response.content if hasattr(response, "content") else str(response)
        return {"summary": content, "insights": []}
