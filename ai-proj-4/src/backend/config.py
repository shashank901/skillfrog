from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class Settings:
    """Application configuration sourced from environment variables."""

    app_name: str = field(default="AI Data Quality Validation Agent")
    environment: str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "local"))
    host: str = field(default_factory=lambda: os.getenv("HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("PORT", "8200")))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))

    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///./quality_reports.db"))

    data_root: Path = field(default_factory=lambda: Path(os.getenv("DATA_ROOT", "data/samples")))

    openai_api_key: Optional[str] = field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    model_name: str = field(default_factory=lambda: os.getenv("MODEL_NAME", "gpt-4o-mini"))
    use_fake_llm: bool = field(default_factory=lambda: os.getenv("USE_FAKE_LLM", "1") == "1")

    missing_threshold: float = field(default_factory=lambda: float(os.getenv("MISSING_THRESHOLD", "0.05")))
    outlier_zscore: float = field(default_factory=lambda: float(os.getenv("OUTLIER_ZSCORE", "3.0")))
    duplicate_tolerance: int = field(default_factory=lambda: int(os.getenv("DUPLICATE_TOLERANCE", "0")))

    def ensure_directories(self) -> None:
        self.data_root.mkdir(parents=True, exist_ok=True)


def load_settings() -> Settings:
    settings = Settings()
    settings.ensure_directories()
    return settings
