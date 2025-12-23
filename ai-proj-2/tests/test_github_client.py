from __future__ import annotations

import httpx
import pytest

from backend.config import Settings
from backend.github_client import GitHubClient


class DummyResponse:
    def __init__(self, status_code: int, text: str):
        self.status_code = status_code
        self.text = text


class DummyClient:
    def __init__(self, response: DummyResponse):
        self.response = response
        self.requested = None

    def get(self, url, headers=None, params=None):
        self.requested = (url, headers, params)
        return self.response

    def close(self):
        pass


@pytest.fixture
def settings():
    return Settings(github_token="token", github_api_url="https://api.github.com")


def test_fetch_file_success(monkeypatch, settings):
    client = GitHubClient(settings)
    dummy = DummyClient(DummyResponse(200, "print('hi')"))
    monkeypatch.setattr(client, "_client", dummy)
    content = client.fetch_file("org/repo", "path.py", "refs/head")
    assert content == "print('hi')"


def test_fetch_file_failure(monkeypatch, settings):
    client = GitHubClient(settings)
    dummy = DummyClient(DummyResponse(404, "not found"))
    monkeypatch.setattr(client, "_client", dummy)
    content = client.fetch_file("org/repo", "missing.py")
    assert content is None
