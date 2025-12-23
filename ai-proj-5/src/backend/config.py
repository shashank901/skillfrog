from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class Settings:
    """Application configuration loaded from environment variables."""

    app_name: str = field(default="Multi-Agent Research Assistant")
    environment: str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "local"))
    host: str = field(default_factory=lambda: os.getenv("HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("PORT", "8300")))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))

    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///./research_reports.db"))
    data_cache_path: Path = field(default_factory=lambda: Path(os.getenv("DATA_CACHE_PATH", "data/samples/search_cache.json")))

    openai_api_key: Optional[str] = field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    serpapi_api_key: Optional[str] = field(default_factory=lambda: os.getenv("SERPAPI_API_KEY"))

    use_fake_llm: bool = field(default_factory=lambda: os.getenv("USE_FAKE_LLM", "1") == "1")
    use_fake_search: bool = field(default_factory=lambda: os.getenv("USE_FAKE_SEARCH", "1") == "1")
    default_max_sources: int = field(default_factory=lambda: int(os.getenv("DEFAULT_MAX_SOURCES", "5")))

    def ensure_directories(self) -> None:
        if self.data_cache_path.parent:
            self.data_cache_path.parent.mkdir(parents=True, exist_ok=True)


def load_settings() -> Settings:
    settings = Settings()
    settings.ensure_directories()
    return settings
