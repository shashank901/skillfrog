from __future__ import annotations

import json
import sys
from pathlib import Path

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
    db_path = tmp_path / "reports.db"
    cache = tmp_path / "cache.json"
    cache.write_text(json.dumps({"queries": []}), encoding="utf-8")
    settings = Settings(
        environment="test",
        host="127.0.0.1",
        port=18300,
        database_url=f"sqlite:///{db_path}",
        data_cache_path=cache,
        use_fake_llm=True,
        use_fake_search=True,
    )
    settings.ensure_directories()
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
