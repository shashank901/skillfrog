from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx


class FinanceApiClient:
    """HTTP client for interacting with the FastAPI backend."""

    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url.rstrip("/")

    def get_users(self) -> List[Dict[str, Any]]:
        response = httpx.get(f"{self.base_url}/users", timeout=10)
        response.raise_for_status()
        return response.json()

    def get_history(self, user_id: int) -> List[Dict[str, Any]]:
        response = httpx.get(f"{self.base_url}/history/{user_id}", timeout=10)
        response.raise_for_status()
        return response.json()["items"]

    def recommend(self, user_id: int, question: Optional[str] = None) -> Dict[str, Any]:
        payload = {"user_id": user_id, "question": question}
        response = httpx.post(f"{self.base_url}/recommend", json=payload, timeout=30)
        response.raise_for_status()
        return response.json()

    def ingest(self, path: Optional[str] = None) -> Dict[str, Any]:
        payload = {"path": path}
        response = httpx.post(f"{self.base_url}/ingest", json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
