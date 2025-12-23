from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Tuple

from sqlmodel import Session, select

from .models import Conversation, Goal, Transaction, User


class FinanceService:
    """Business logic for financial calculations and persistence."""

    def __init__(self, session: Session):
        self.session = session

    # -------- User & Data retrieval -------- #
    def get_users(self) -> List[User]:
        return self.session.exec(select(User)).all()

    def get_user(self, user_id: int) -> User:
        user = self.session.get(User, user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        return user

    def get_transactions(self, user_id: int) -> List[Transaction]:
        return self.session.exec(select(Transaction).where(Transaction.user_id == user_id)).all()

    def get_goals(self, user_id: int) -> List[Goal]:
        return self.session.exec(select(Goal).where(Goal.user_id == user_id)).all()

    def get_recent_conversations(self, user_id: int, limit: int = 5) -> List[Conversation]:
        return (
            self.session.exec(
                select(Conversation)
                .where(Conversation.user_id == user_id)
                .order_by(Conversation.created_at.desc())
                .limit(limit)
            )
            .all()
        )

    # -------- Calculations -------- #
    def calculate_financial_snapshot(self, user_id: int) -> Dict[str, float]:
        transactions = self.get_transactions(user_id)
        income = sum(t.amount for t in transactions if t.type == "income")
        expenses = sum(t.amount for t in transactions if t.type != "income")
        category_totals: Dict[str, float] = defaultdict(float)
        for txn in transactions:
            if txn.type != "income":
                category_totals[txn.category] += txn.amount

        savings_rate = 0.0
        disposable = income - expenses
        if income > 0:
            savings_rate = max(disposable / income, 0)

        return {
            "income": income,
            "expenses": expenses,
            "disposable": disposable,
            "savings_rate": savings_rate,
            "category_totals": dict(category_totals),
        }

    def build_goal_summary(self, user_id: int) -> List[str]:
        summaries = []
        for goal in self.get_goals(user_id):
            monthly_target = goal.target_amount / max(goal.timeline_months, 1)
            summaries.append(
                f"{goal.name}: target ${goal.target_amount:,.0f} in {goal.timeline_months} months "
                f"(~${monthly_target:,.0f}/month)."
            )
        return summaries

    def determine_investment_allocation(self, risk_tolerance: str) -> List[Tuple[str, int]]:
        presets = {
            "conservative": [("High-yield savings", 50), ("Bond ETF", 30), ("Broad market ETF", 20)],
            "moderate": [("High-yield savings", 30), ("Bond ETF", 30), ("Broad market ETF", 30), ("Thematic ETF", 10)],
            "aggressive": [("High-yield savings", 15), ("Broad market ETF", 45), ("International ETF", 25), ("Emerging markets", 15)],
        }
        return presets.get(risk_tolerance.lower(), presets["moderate"])

    # -------- Persistence -------- #
    def record_conversation(self, user_id: int, question: str, answer: str) -> Conversation:
        convo = Conversation(user_id=user_id, question=question, answer=answer)
        self.session.add(convo)
        self.session.commit()
        self.session.refresh(convo)
        return convo
