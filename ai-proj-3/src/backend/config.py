from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class Settings:
    """Application configuration loaded from environment variables."""

    app_name: str = field(default="Telecom Support RAG Agent")
    environment: str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "local"))
    host: str = field(default_factory=lambda: os.getenv("HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("PORT", "8000")))
    openai_api_key: Optional[str] = field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    gemini_api_key: Optional[str] = field(default_factory=lambda: os.getenv("GEMINI_API_KEY"))
    model_provider: str = field(default_factory=lambda: os.getenv("MODEL_PROVIDER", "openai"))
    model_name: str = field(default_factory=lambda: os.getenv("MODEL_NAME", "gpt-4o-mini"))
    gemini_model_name: str = field(default_factory=lambda: os.getenv("GEMINI_MODEL_NAME", "models/gemini-1.5-flash"))
    vector_store_path: Path = field(
        default_factory=lambda: Path(os.getenv("VECTOR_STORE_PATH", "storage/chroma"))
    )
    docs_path: Path = field(default_factory=lambda: Path(os.getenv("DOCUMENTS_PATH", "data/sample_faqs")))
    chunk_size: int = field(default_factory=lambda: int(os.getenv("CHUNK_SIZE", "800")))
    chunk_overlap: int = field(default_factory=lambda: int(os.getenv("CHUNK_OVERLAP", "150")))
    top_k: int = field(default_factory=lambda: int(os.getenv("TOP_K", "4")))
    chat_history_limit: int = field(default_factory=lambda: int(os.getenv("CHAT_HISTORY_LIMIT", "50")))
    frontend_origin: str = field(default_factory=lambda: os.getenv("FRONTEND_ORIGIN", "*"))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    enable_fake_embeddings: bool = field(default_factory=lambda: os.getenv("USE_FAKE_EMBEDDINGS", "0") == "1")
    enable_fake_llm: bool = field(default_factory=lambda: os.getenv("USE_FAKE_LLM", "0") == "1")
    chroma_collection: str = field(default_factory=lambda: os.getenv("CHROMA_COLLECTION", "telecom_support_docs"))

    def ensure_directories(self) -> None:
        """Ensure directories referenced in settings exist."""
        self.vector_store_path.mkdir(parents=True, exist_ok=True)
        self.docs_path.mkdir(parents=True, exist_ok=True)


def load_settings() -> Settings:
    """Load settings from environment and ensure necessary folders exist."""
    settings = Settings()
    settings.ensure_directories()
    return settings
