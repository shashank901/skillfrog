from __future__ import annotations

from backend.schemas import ResearchRequest


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_research_endpoint(client):
    payload = {"topic": "test topic", "max_sources": 2}
    response = client.post("/research", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["topic"] == "test topic"
    assert "summary_md" in data


def test_reports_listing(client):
    client.post("/research", json={"topic": "second topic"})
    response = client.get("/reports", params={"limit": 5})
    assert response.status_code == 200
    assert response.json()["items"], "Expected at least one report"
