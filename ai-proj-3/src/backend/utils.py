from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

try:
    from langchain_community.document_loaders import PyPDFLoader, TextLoader
except ImportError as exc:  # pragma: no cover - handled during install
    raise RuntimeError(
        "Missing langchain_community dependencies. "
        "Ensure `langchain-community` is installed."
    ) from exc


SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md"}


def load_and_split_documents(
    directory: Path,
    chunk_size: int,
    chunk_overlap: int,
) -> Tuple[List[Document], Dict[str, int]]:
    """Load supported documents from directory and split them into chunks.

    Returns both the list of chunked documents and ingestion metrics.
    """
    directory = directory.resolve()
    if not directory.exists():
        raise FileNotFoundError(f"Source directory {directory} does not exist")

    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    documents: List[Document] = []
    metrics: Dict[str, int] = defaultdict(int)

    for file_path in directory.rglob("*"):
        if file_path.is_dir():
            continue
        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        loaded_docs = _load_file(file_path)
        metrics["files"] += 1
        metrics["pages"] += len(loaded_docs)
        for doc in loaded_docs:
            doc.metadata.setdefault("source", str(file_path))
            doc.metadata.setdefault("file_name", file_path.name)
        chunks = splitter.split_documents(loaded_docs)
        for idx, chunk in enumerate(chunks):
            chunk.metadata["chunk_id"] = f"{file_path.stem}-{idx}"
        documents.extend(chunks)
        metrics["chunks"] += len(chunks)

    metrics.setdefault("files", 0)
    metrics.setdefault("pages", 0)
    metrics.setdefault("chunks", 0)

    if not documents:
        raise ValueError(f"No supported documents found in {directory}")

    return documents, dict(metrics)


def _load_file(path: Path) -> List[Document]:
    """Load a single file as LangChain documents depending on extension."""
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        loader = PyPDFLoader(str(path))
        return loader.load()
    if suffix in {".txt", ".md"}:
        loader = TextLoader(str(path), autodetect_encoding=True)
        return loader.load()
    raise ValueError(f"Unsupported extension: {suffix}")


def format_sources(documents: Iterable[Document]) -> List[Dict[str, str]]:
    """Format LangChain documents into user-friendly citation metadata."""
    formatted = []
    for rank, doc in enumerate(documents, start=1):
        metadata = doc.metadata or {}
        formatted.append(
            {
                "rank": rank,
                "file": metadata.get("file_name", metadata.get("source", "unknown")),
                "page": str(metadata.get("page", "n/a")),
                "chunk_id": metadata.get("chunk_id", ""),
                "source": metadata.get("source", ""),
            }
        )
    return formatted
