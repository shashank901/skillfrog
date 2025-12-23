from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from .config import load_settings
from .pipeline import RAGPipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest telecom FAQ documents into Chroma.")
    parser.add_argument(
        "--source",
        type=str,
        default=None,
        help="Directory containing PDF/TXT/MD documents. Defaults to DOCUMENTS_PATH.",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing vector store before ingesting.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = load_settings()

    if args.reset and settings.vector_store_path.exists():
        shutil.rmtree(settings.vector_store_path, ignore_errors=True)
        settings.vector_store_path.mkdir(parents=True, exist_ok=True)

    pipeline = RAGPipeline(settings=settings)
    metrics = pipeline.ingest(Path(args.source) if args.source else None)
    print(json.dumps({"message": "ingestion_complete", "metrics": metrics}, indent=2))


if __name__ == "__main__":  # pragma: no cover - CLI entry
    main()
