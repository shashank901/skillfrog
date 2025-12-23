from __future__ import annotations

import logging
from typing import Optional

import httpx

from .config import Settings

LOGGER = logging.getLogger(__name__)


class GitHubClient:
    """Simple GitHub REST API client for fetching file contents."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._client = httpx.Client(base_url=settings.github_api_url, timeout=10.0)

    def fetch_file(self, repo: str, path: str, ref: Optional[str] = None) -> Optional[str]:
        if not repo or not path:
            raise ValueError("Repository and path are required")

        headers = {"Accept": "application/vnd.github.v3.raw"}
        if self.settings.github_token:
            headers["Authorization"] = f"token {self.settings.github_token}"

        params = {"ref": ref} if ref else {}
        url = f"/repos/{repo}/contents/{path}"
        try:
            response = self._client.get(url, headers=headers, params=params)
            if response.status_code == 200:
                return response.text
            LOGGER.warning("GitHub fetch failed %s %s", response.status_code, response.text)
            return None
        except httpx.HTTPError as exc:
            LOGGER.exception("GitHub request error: %s", exc)
            return None

    def close(self) -> None:
        self._client.close()
