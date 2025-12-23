from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class Settings:
    """Application settings populated from environment variables."""

    app_name: str = field(default="AI Code Reviewer Agent")
    environment: str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "local"))
    host: str = field(default_factory=lambda: os.getenv("HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("PORT", "8100")))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))

    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///./reviews.db"))

    openai_api_key: Optional[str] = field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    model_name: str = field(default_factory=lambda: os.getenv("MODEL_NAME", "gpt-4o-mini"))
    use_fake_llm: bool = field(default_factory=lambda: os.getenv("USE_FAKE_LLM", "1") == "1")

    github_token: Optional[str] = field(default_factory=lambda: os.getenv("GITHUB_TOKEN"))
    github_api_url: str = field(default_factory=lambda: os.getenv("GITHUB_API_URL", "https://api.github.com"))

    max_issues: int = field(default_factory=lambda: int(os.getenv("MAX_ISSUES", "20")))
    severity_threshold: str = field(default_factory=lambda: os.getenv("SEVERITY_THRESHOLD", "low"))

    data_dir: Path = field(default_factory=lambda: Path(os.getenv("DATA_DIR", "data")))

    def ensure_directories(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)


def load_settings() -> Settings:
    settings = Settings()
    settings.ensure_directories()
    return settings
