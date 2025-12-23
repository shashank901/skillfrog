from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterator

import pytest
from fastapi.testclient import TestClient

BASE_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from backend.app import create_app, get_settings  # noqa: E402
from backend.config import Settings  # noqa: E402
from backend.db import Database  # noqa: E402
from backend.ingestion import ingest_from_path  # noqa: E402
from backend.services import FinanceService  # noqa: E402


@pytest.fixture
def sample_csv(tmp_path: Path) -> Path:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    csv_path = data_dir / "sample_transactions.csv"
    csv_path.write_text(
        """user_id,name,income_monthly,risk_tolerance,goal_name,goal_target,goal_timeline_months,category,type,amount,month
1,Alice,6000,moderate,Emergency Fund,9000,12,Rent,expense,1800,2025-01
1,Alice,6000,moderate,Emergency Fund,9000,12,Groceries,expense,520,2025-01
1,Alice,6000,moderate,Emergency Fund,9000,12,Income,income,6000,2025-01
1,Alice,6000,moderate,Emergency Fund,9000,12,Travel,expense,300,2025-01
""",
        encoding="utf-8",
    )
    return csv_path


@pytest.fixture
def test_settings(sample_csv: Path) -> Settings:
    data_dir = sample_csv.parent
    settings = Settings(
        environment="test",
        host="127.0.0.1",
        port=18001,
        database_url=f"sqlite:///{data_dir.parent/'finance.db'}",
        openai_api_key=None,
        use_fake_llm=True,
        data_dir=data_dir,
        frontend_origin="http://test",
        log_level="DEBUG",
    )
    settings.ensure_directories()
    return settings


@pytest.fixture
def database(test_settings: Settings) -> Database:
    db = Database(settings=test_settings)
    db.create_schema()
    return db


@pytest.fixture
def session(database: Database) -> Iterator:
    with database.session() as session:
        yield session


@pytest.fixture
def finance_service(session) -> FinanceService:
    return FinanceService(session=session)


@pytest.fixture(autouse=True)
def seed_data(finance_service: FinanceService, test_settings: Settings, sample_csv: Path):
    ingest_from_path(test_settings, finance_service.session, sample_csv)


@pytest.fixture
def app(test_settings: Settings, database: Database):
    application = create_app(settings=test_settings)
    # Override settings dependency for tests
    application.dependency_overrides[get_settings] = lambda: test_settings
    return application


@pytest.fixture
def client(app) -> TestClient:
    return TestClient(app)
