from __future__ import annotations

import logging
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from src.backend import create_app  # noqa: E402
from src.backend.config import load_settings  # noqa: E402

settings = load_settings()
app = create_app(settings=settings)


def main() -> None:
    import uvicorn

    logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
    uvicorn.run("main:app", host=settings.host, port=settings.port, log_level=settings.log_level.lower())


if __name__ == "__main__":  # pragma: no cover
    main()
