from __future__ import annotations


def test_users_endpoint(client):
    response = client.get("/users")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["name"] == "Alice"


def test_recommend_endpoint(client):
    response = client.post("/recommend", json={"user_id": 1, "question": "How to improve savings?"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["recommended_actions"]
    assert payload["monthly_projection"] >= 0


def test_history_endpoint(client):
    client.post("/recommend", json={"user_id": 1, "question": "Plan"})
    history_response = client.get("/history/1")
    assert history_response.status_code == 200
    assert history_response.json()["items"], "History should contain conversations"
