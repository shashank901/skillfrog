from __future__ import annotations

from backend.schemas import DatasetRequest


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_validate_inline(client):
    payload = {
        "dataset_name": "inline",
        "records": [
            {"a": 1, "b": 2},
            {"a": None, "b": 3},
            {"a": 100, "b": 2},
        ],
    }
    response = client.post("/validate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["issues"]
    assert data["dataset_name"] == "inline"


def test_validate_missing_payload(client):
    response = client.post("/validate", json={"dataset_name": "bad"})
    assert response.status_code == 400
