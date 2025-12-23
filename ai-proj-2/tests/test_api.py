from __future__ import annotations


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_review_endpoint(client, sample_code):
    payload = {"code": sample_code}
    response = client.post("/review", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "issues" in data


def test_review_history(client, sample_code):
    client.post("/review", json={"code": sample_code})
    response = client.get("/reviews")
    assert response.status_code == 200
    assert response.json()["items"], "Expected at least one review"
