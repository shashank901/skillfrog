from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List

from langchain.schema import BaseMessage

try:
    from langchain_openai import ChatOpenAI
except ImportError:  # pragma: no cover
    ChatOpenAI = None  # type: ignore

from .config import Settings
from .services import FinanceService

LOGGER = logging.getLogger(__name__)


@dataclass
class RecommendationResult:
    summary: str
    recommended_actions: List[str]
    investment_split: List[str]
    savings_rate: float
    monthly_projection: float


class FinanceAdvisorAgent:
    """LangChain-powered advisor with deterministic fallback."""

    def __init__(self, settings: Settings, service: FinanceService):
        self.settings = settings
        self.service = service
        self.llm = self._init_llm(settings)

    def _init_llm(self, settings: Settings):
        if settings.use_fake_llm or not settings.openai_api_key:
            LOGGER.info("Using deterministic fallback advisor (no API key or fake LLM enabled).")
            return None
        if ChatOpenAI is None:
            LOGGER.warning("langchain-openai not installed; using fallback advisor.")
            return None
        LOGGER.info("Using OpenAI model %s", settings.model_name)
        return ChatOpenAI(model=settings.model_name, temperature=0.2, api_key=settings.openai_api_key)

    def recommend(self, user_id: int, question: str) -> RecommendationResult:
        user = self.service.get_user(user_id)
        snapshot = self.service.calculate_financial_snapshot(user_id)
        goal_summary = self.service.build_goal_summary(user_id)
        allocation = self.service.determine_investment_allocation(user.risk_tolerance)
        investment_split = [f"{name}: {weight}%" for name, weight in allocation]
        memory = self.service.get_recent_conversations(user_id, limit=self.settings.memory_window)

        prompt = self._build_prompt(
            user_name=user.name,
            risk_tolerance=user.risk_tolerance,
            question=question,
            snapshot=snapshot,
            goals=goal_summary,
            allocation=investment_split,
            history=memory,
        )

        if self.llm:
            try:
                response: BaseMessage = self.llm.invoke(prompt)  # type: ignore[assignment]
                summary = response.content.strip()
            except Exception as exc:  # pragma: no cover
                LOGGER.exception("LLM invocation failed: %s", exc)
                summary = self._fallback_summary(snapshot, goal_summary, investment_split, question)
        else:
            summary = self._fallback_summary(snapshot, goal_summary, investment_split, question)

        recommended_actions = self._extract_actions(summary, snapshot, goal_summary)
        monthly_projection = max(snapshot["disposable"], 0)

        result = RecommendationResult(
            summary=summary,
            recommended_actions=recommended_actions,
            investment_split=investment_split,
            savings_rate=round(snapshot["savings_rate"], 2),
            monthly_projection=round(monthly_projection, 2),
        )
        self.service.record_conversation(user_id, question, summary)
        return result

    def _build_prompt(
        self,
        user_name: str,
        risk_tolerance: str,
        question: str,
        snapshot,
        goals,
        allocation,
        history,
    ) -> str:
        history_block = "\n".join(
            f"User: {item.question}\nAdvisor: {item.answer}" for item in reversed(history)
        )
        goals_block = "\n".join(goals) or "No explicit goals recorded."
        expenses_lines = "\n".join(
            f"- {category}: ${amount:,.0f}" for category, amount in snapshot["category_totals"].items()
        )

        return (
            "You are a certified financial planner focused on practical, compliant advice.\n"
            "Use the data provided to craft a concise plan with numbered action items and a tone that is encouraging yet realistic.\n"
            f"Client: {user_name}\nRisk tolerance: {risk_tolerance}\n"
            f"Question: {question}\n"
            f"Monthly income: ${snapshot['income']:,.0f}\n"
            f"Monthly expenses: ${snapshot['expenses']:,.0f}\n"
            f"Savings rate: {snapshot['savings_rate']*100:.1f}%\n"
            f"Disposable income: ${snapshot['disposable']:,.0f}\n"
            f"Spending by category:\n{expenses_lines or '- No expenses recorded'}\n"
            f"Goals:\n{goals_block}\n"
            f"Suggested investment allocation: {', '.join(allocation)}\n"
            f"Conversation memory:\n{history_block or 'None'}\n"
            "Structure your response with:\n"
            "1. Overview paragraph summarizing financial health.\n"
            "2. Numbered list of recommendations focused on budgeting and savings.\n"
            "3. Suggested investment allocation reiterating percentages.\n"
            "4. A motivational closing sentence.\n"
        )

    def _fallback_summary(
        self, snapshot, goals: List[str], allocation: List[str], question: str
    ) -> str:
        expense_focus = sorted(snapshot["category_totals"].items(), key=lambda item: item[1], reverse=True)
        top_spend = ", ".join(f"{cat} ${amt:,.0f}" for cat, amt in expense_focus[:3]) or "No major expenses logged."
        goal_sentence = " ".join(goals) if goals else "No goals captured yet. Encourage the user to define at least one savings goal."
        return (
            f"Your disposable income is approximately ${snapshot['disposable']:,.0f} per month and your savings rate is "
            f"{snapshot['savings_rate']*100:.1f}%. Top spending areas: {top_spend}. "
            f"{goal_sentence} Focus on the following actions to address: {question}. "
            f"Recommended allocation: {', '.join(allocation)}."
        )

    def _extract_actions(self, summary: str, snapshot, goals: List[str]) -> List[str]:
        actions = []
        if snapshot["savings_rate"] < 0.2:
            actions.append("Cap discretionary categories at 80% of current spend to reach a 20% savings rate.")
        if snapshot["disposable"] > 0:
            actions.append("Automate transfers of disposable income into high-yield savings on payday.")
        if goals:
            actions.append("Track progress toward each goal monthly and adjust contributions if off pace.")
        if not actions:
            actions.append("Maintain current budget and revisit goals quarterly.")
        # deduplicate while preserving order
        seen = set()
        unique_actions = []
        for act in actions:
            if act not in seen:
                unique_actions.append(act)
                seen.add(act)
        return unique_actions
