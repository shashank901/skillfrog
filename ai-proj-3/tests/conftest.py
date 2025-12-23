from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

BASE_DIR = Path(__file__).resolve().parents[1]
SRC_PATH = BASE_DIR / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from src.backend.app import create_app  # noqa: E402
from src.backend.config import Settings  # noqa: E402
from src.backend.pipeline import RAGPipeline  # noqa: E402


@pytest.fixture
def sample_docs(tmp_path: Path) -> Path:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "roaming.txt").write_text(
        (
            "International roaming activation requires the account to be in good standing. "
            "Customers must notify support 48 hours before travel to enable roaming and "
            "confirm daily spending limits."
        ),
        encoding="utf-8",
    )
    (docs_dir / "billing.txt").write_text(
        (
            "Billing disputes must be submitted within 30 days with supporting case references. "
            "Resolutions are communicated by email within 5 business days."
        ),
        encoding="utf-8",
    )
    return docs_dir


@pytest.fixture
def test_settings(tmp_path: Path, sample_docs: Path) -> Settings:
    storage_dir = tmp_path / "storage"
    settings = Settings(
        vector_store_path=storage_dir,
        docs_path=sample_docs,
        enable_fake_embeddings=True,
        enable_fake_llm=True,
        top_k=2,
        chunk_size=256,
        chunk_overlap=40,
        frontend_origin="http://test",
        environment="test",
    )
    settings.ensure_directories()
    return settings


@pytest.fixture
def pipeline(test_settings: Settings) -> RAGPipeline:
    pipe = RAGPipeline(settings=test_settings)
    pipe.ingest(test_settings.docs_path)
    return pipe


@pytest.fixture
def client(test_settings: Settings) -> TestClient:
    app = create_app(settings=test_settings)
    app.state.pipeline.ingest(test_settings.docs_path)
    return TestClient(app)
