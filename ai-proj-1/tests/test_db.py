from __future__ import annotations

from sqlmodel import select

from backend.models import Goal, Transaction, User


def test_users_persisted(session):
    users = session.exec(select(User)).all()
    assert users
    assert users[0].name == "Alice"


def test_transactions_loaded(session):
    transactions = session.exec(select(Transaction)).all()
    expense_total = sum(t.amount for t in transactions if t.type != "income")
    income_total = sum(t.amount for t in transactions if t.type == "income")
    assert income_total > expense_total * 0.5


def test_goal_created(session):
    goal = session.exec(select(Goal)).first()
    assert goal
    assert goal.target_amount == 9000
