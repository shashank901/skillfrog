from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_root_includes_port_and_message():
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["message"] == "Lab container is running"
    assert "port" in data


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_items():
    res = client.get("/items")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert data[0]["id"] == "notebook"


def test_echo():
    payload = {"foo": "bar"}
    res = client.post("/echo", json={"payload": payload})
    assert res.status_code == 200
    data = res.json()
    assert data["payload"] == payload
