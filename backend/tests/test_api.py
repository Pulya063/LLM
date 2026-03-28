from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
HEADERS = {"x-api-key": "debug-assistant-key"}


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_chat_contract():
    payload = {"message": "How do I debug mismatched JSON responses?", "top_k": 2}
    response = client.post("/api/chat", json=payload, headers=HEADERS)
    assert response.status_code == 200
    body = response.json()
    assert "answer" in body
    assert "sources" in body
    assert "trace_id" in body


def test_legacy_bug_endpoint_shape():
    payload = {"message": "Show legacy shape", "top_k": 1}
    response = client.post("/api/chat/legacy", json=payload, headers=HEADERS)
    assert response.status_code == 200
    body = response.json()
    assert "response" in body
    assert "source_items" in body
    assert "request_id" in body
