from __future__ import annotations

import csv
import argparse
import json
from pathlib import Path
from typing import Dict, Iterable, List

from sqlmodel import Session, select

from .config import Settings
from .models import Goal, Transaction, User


def load_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [row for row in reader]


def ingest_transactions(session: Session, rows: Iterable[Dict[str, str]]) -> Dict[str, int]:
    metrics = {"users": 0, "transactions": 0, "goals": 0}
    seen_users = {}

    for row in rows:
        user_id = int(row["user_id"])
        if user_id not in seen_users:
            user = session.get(User, user_id)
            if not user:
                user = User(
                    id=user_id,
                    name=row["name"],
                    income_monthly=float(row["income_monthly"]),
                    risk_tolerance=row.get("risk_tolerance", "moderate"),
                )
                session.add(user)
                metrics["users"] += 1
            seen_users[user_id] = user

            # Goals might be repeated in CSV; ensure uniqueness per goal name
            goal_name = row.get("goal_name")
            if goal_name:
                existing_goal = session.exec(
                    select(Goal).where(Goal.user_id == user_id, Goal.name == goal_name)
                ).first()
                if not existing_goal:
                    goal = Goal(
                        user_id=user_id,
                        name=goal_name,
                        target_amount=float(row.get("goal_target", 0) or 0),
                        timeline_months=int(row.get("goal_timeline_months", 12) or 12),
                    )
                    session.add(goal)
                    metrics["goals"] += 1

        transaction = Transaction(
            user_id=user_id,
            category=row.get("category", "uncategorized"),
            amount=float(row["amount"]),
            type=row.get("type", "expense"),
            month=row.get("month", "2025-01"),
        )
        session.add(transaction)
        metrics["transactions"] += 1

    session.commit()
    return metrics


def ingest_from_path(settings: Settings, session: Session, path: Path | None = None) -> Dict[str, int]:
    target = path or (settings.data_dir / "sample_transactions.csv")
    if not target.exists():
        raise FileNotFoundError(f"CSV file not found: {target}")
    rows = load_csv(target)
    if not rows:
        raise ValueError(f"CSV file {target} is empty.")
    return ingest_transactions(session, rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest finance transaction data into SQLite")
    parser.add_argument("--path", type=str, default=None, help="Optional CSV file path")
    parser.add_argument("--seed", action="store_true", help="Shortcut to load sample data")
    return parser.parse_args()


def main() -> None:  # pragma: no cover - CLI entry
    from .db import Database  # local import to avoid circular dependency

    args = parse_args()
    settings = Settings()
    settings.ensure_directories()
    database = Database(settings)
    database.create_schema()
    with database.session() as session:
        target = Path(args.path) if args.path else (settings.data_dir / "sample_transactions.csv")
        metrics = ingest_from_path(settings, session, target)
        print(json.dumps({"status": "completed", "metrics": metrics}, indent=2))


if __name__ == "__main__":  # pragma: no cover
    main()
