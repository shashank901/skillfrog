from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient

BASE_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from backend.app import create_app, get_settings  # noqa: E402
from backend.config import Settings  # noqa: E402
from backend.db import Database  # noqa: E402


@pytest.fixture
def tmp_settings(tmp_path: Path) -> Settings:
    db_path = tmp_path / "quality_reports.db"
    settings = Settings(
        environment="test",
        host="127.0.0.1",
        port=18200,
        database_url=f"sqlite:///{db_path}",
        use_fake_llm=True,
        data_root=tmp_path,
    )
    settings.ensure_directories()
    sample = tmp_path / "retail.csv"
    pd.DataFrame(
        [
            {"a": 1, "b": 2},
            {"a": 1, "b": None},
            {"a": 1000, "b": 2},
        ]
    ).to_csv(sample, index=False)
    return settings


@pytest.fixture
def database(tmp_settings: Settings) -> Database:
    db = Database(tmp_settings)
    db.create_schema()
    return db


@pytest.fixture
def app(tmp_settings: Settings, database: Database):
    application = create_app(settings=tmp_settings)
    application.dependency_overrides[get_settings] = lambda: tmp_settings
    return application


@pytest.fixture
def client(app) -> TestClient:
    return TestClient(app)
