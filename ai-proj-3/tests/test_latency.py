from __future__ import annotations

import time


def test_chat_latency_under_budget(client):
    start = time.perf_counter()
    response = client.post("/chat", json={"question": "How are billing disputes handled?"})
    elapsed_ms = (time.perf_counter() - start) * 1000
    assert response.status_code == 200
    assert elapsed_ms < 1000, f"Chat response exceeded latency budget: {elapsed_ms:.2f}ms"
