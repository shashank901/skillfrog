from __future__ import annotations

from backend.agent import FinanceAdvisorAgent
from backend.services import FinanceService


def test_agent_returns_recommendation(finance_service: FinanceService, test_settings):
    agent = FinanceAdvisorAgent(settings=test_settings, service=finance_service)
    result = agent.recommend(user_id=1, question="How can I save more each month?")
    assert result.summary
    assert result.savings_rate >= 0
    assert result.recommended_actions
    assert any("allocation" in item.lower() or "%" in item for item in result.investment_split)


def test_agent_records_conversation(finance_service: FinanceService, test_settings, session):
    agent = FinanceAdvisorAgent(settings=test_settings, service=finance_service)
    agent.recommend(user_id=1, question="What's my disposable income?")
    history = finance_service.get_recent_conversations(1)
    assert history
    assert history[0].question == "What's my disposable income?"
