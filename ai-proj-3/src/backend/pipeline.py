from __future__ import annotations

import hashlib
import logging
import threading
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Deque, Dict, List, Optional

from langchain.schema import Document
from langchain.embeddings.base import Embeddings

try:
    from langchain_community.vectorstores import Chroma
except ImportError as exc:  # pragma: no cover - library should be installed via requirements
    raise RuntimeError("Chroma dependencies are missing; install `chromadb`.") from exc

from .config import Settings
from .utils import format_sources, load_and_split_documents

LOGGER = logging.getLogger(__name__)


@dataclass
class HashEmbeddingFunction(Embeddings):
    """Deterministic embedding fallback using SHA-based hashing."""

    dimension: int = 384

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._vectorize(text) for text in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._vectorize(text)

    def _vectorize(self, text: str) -> List[float]:
        seed = text.strip() or "empty"
        vector: List[float] = []
        counter = 0
        while len(vector) < self.dimension:
            digest = hashlib.sha256(f"{seed}-{counter}".encode("utf-8")).digest()
            vector.extend([byte / 255 for byte in digest])
            counter += 1
        return vector[: self.dimension]


class RAGPipeline:
    """Orchestrates ingestion, retrieval, and answer generation."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._lock = threading.Lock()
        self._history: Deque[Dict[str, object]] = deque(maxlen=settings.chat_history_limit)
        self._embedding = self._build_embedding()
        self._vectorstore = self._build_vectorstore()
        self._llm = self._build_llm()

    # ---------------------------
    # Builders
    # ---------------------------
    def _build_embedding(self) -> Embeddings:
        if not self.settings.enable_fake_embeddings and self.settings.openai_api_key:
            try:
                from langchain_openai import OpenAIEmbeddings
            except ImportError:
                LOGGER.warning("langchain-openai not installed; falling back to hash embeddings.")
            else:
                LOGGER.info("Using OpenAI embeddings with model %s", self.settings.model_name)
                return OpenAIEmbeddings(model=self.settings.model_name, api_key=self.settings.openai_api_key)

        if not self.settings.enable_fake_embeddings and self.settings.gemini_api_key:
            try:
                from langchain_google_genai import GoogleGenerativeAIEmbeddings
            except ImportError:
                LOGGER.warning("langchain-google-genai not installed; using hash embeddings.")
            else:
                LOGGER.info("Using Gemini embeddings with model %s", self.settings.gemini_model_name)
                return GoogleGenerativeAIEmbeddings(
                    model=self.settings.gemini_model_name,
                    google_api_key=self.settings.gemini_api_key,
                )

        LOGGER.info("Using deterministic hash embeddings.")
        return HashEmbeddingFunction()

    def _build_vectorstore(self) -> Chroma:
        persist_dir = str(self.settings.vector_store_path)
        LOGGER.info("Initializing Chroma vector store at %s", persist_dir)
        return Chroma(
            collection_name=self.settings.chroma_collection,
            embedding_function=self._embedding,
            persist_directory=persist_dir,
        )

    def _build_llm(self):
        if self.settings.enable_fake_llm:
            LOGGER.info("Fake LLM enabled; using heuristic responses.")
            return None

        if self.settings.openai_api_key and self.settings.model_provider.lower() == "openai":
            try:
                from langchain_openai import ChatOpenAI
            except ImportError:
                LOGGER.warning("langchain-openai not installed; defaulting to heuristic responses.")
            else:
                LOGGER.info("Using OpenAI Chat model %s", self.settings.model_name)
                return ChatOpenAI(
                    model=self.settings.model_name,
                    temperature=0.2,
                    api_key=self.settings.openai_api_key,
                )

        if self.settings.gemini_api_key:
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
            except ImportError:
                LOGGER.warning("langchain-google-genai not installed; defaulting to heuristic responses.")
            else:
                LOGGER.info("Using Gemini Chat model %s", self.settings.gemini_model_name)
                return ChatGoogleGenerativeAI(
                    model=self.settings.gemini_model_name,
                    temperature=0.2,
                    google_api_key=self.settings.gemini_api_key,
                )

        LOGGER.info("No external LLM configured; using heuristic summarizer.")
        return None

    # ---------------------------
    # Pipeline methods
    # ---------------------------
    def ingest(self, source_dir: Optional[Path] = None) -> Dict[str, int]:
        """Ingest documents from the provided directory."""
        directory = Path(source_dir or self.settings.docs_path)
        LOGGER.info("Starting ingestion from %s", directory)
        documents, metrics = load_and_split_documents(
            directory=directory,
            chunk_size=self.settings.chunk_size,
            chunk_overlap=self.settings.chunk_overlap,
        )
        LOGGER.info("Loaded %s chunks from %s files", metrics["chunks"], metrics["files"])
        with self._lock:
            self._vectorstore.add_documents(documents)
            self._vectorstore.persist()

        collection = getattr(self._vectorstore, "_collection", None)
        if collection is not None:  # pragma: no branch - attribute exists in Chroma
            metrics["collection_size"] = collection.count()
        return metrics

    def query(self, question: str) -> Dict[str, object]:
        """Answer a question using retrieval + (optional) generative response."""
        clean_question = question.strip()
        if not clean_question:
            raise ValueError("Question cannot be empty.")

        LOGGER.debug("Received question: %s", clean_question)
        docs = self._vectorstore.similarity_search(clean_question, k=self.settings.top_k)
        if not docs:
            LOGGER.warning("No documents matched the question.")
            return {
                "question": clean_question,
                "answer": "I could not find relevant information in the knowledge base yet.",
                "sources": [],
            }

        answer = self._generate_answer(clean_question, docs)
        sources = format_sources(docs)
        result = {"question": clean_question, "answer": answer, "sources": sources}
        with self._lock:
            self._history.appendleft(result)
        return result

    def history(self, limit: Optional[int] = None) -> List[Dict[str, object]]:
        """Return recent chat history."""
        lim = limit or self.settings.chat_history_limit
        return list(list(self._history)[0:lim])

    def _generate_answer(self, question: str, documents: List[Document]) -> str:
        context = "\n\n".join(
            f"[Source {idx+1}] {doc.page_content.strip()}" for idx, doc in enumerate(documents)
        )
        if self._llm:
            prompt = (
                "You are a telecom customer support policy assistant. Use the context to craft a concise answer.\n"
                "If the answer is not present, politely say you do not know.\n"
                f"Question: {question}\n"
                f"Context:\n{context}\n"
                "Answer with 2-3 sentences and cite sources as [Source #]."
            )
            try:
                response = self._llm.invoke(prompt)  # type: ignore[call-arg]
                if hasattr(response, "content"):
                    return response.content.strip()
                return str(response).strip()
            except Exception as exc:  # pragma: no cover - defensive path
                LOGGER.exception("LLM invocation failed: %s", exc)

        # Deterministic fallback summarizer
        snippets = []
        for idx, doc in enumerate(documents, start=1):
            text = doc.page_content.replace("\n", " ")
            snippets.append(f"[Source {idx}] {text[:220]}...")
        fallback_answer = (
            "Based on the knowledge base, here is what I found: "
            + " ".join(snippets)
            + " If this does not answer the question, consider adding more detailed documents."
        )
        return fallback_answer
