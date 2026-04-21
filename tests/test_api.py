# tests/test_api.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from api.models import ChatResponse


@pytest.fixture
def client():
    mock_orchestrator = MagicMock()
    mock_orchestrator.chat = AsyncMock(
        return_value=ChatResponse(
            conversation_id="test-conv-id",
            response="Found root cause: MS throttling.",
            tools_used=["query_traces"],
            smoke_alert=None,
        )
    )
    mock_orchestrator.get_messages = MagicMock(return_value=[])

    from api.main import create_app
    app = create_app(orchestrator=mock_orchestrator)
    return TestClient(app)


def test_chat_returns_200(client):
    response = client.post(
        "/api/chat",
        json={"message": "Customer Acme has 500 errors since 14:00 UTC"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["conversation_id"] == "test-conv-id"
    assert "throttling" in data["response"].lower()
    assert "query_traces" in data["tools_used"]


def test_chat_with_case_id(client):
    response = client.post(
        "/api/chat",
        json={"message": "Investigate this", "case_id": "SF-12345"},
    )
    assert response.status_code == 200


def test_chat_with_conversation_id(client):
    response = client.post(
        "/api/chat",
        json={"message": "Follow up question", "conversation_id": "existing-conv-id"},
    )
    assert response.status_code == 200


def test_get_messages_returns_200(client):
    response = client.get("/api/conversations/test-conv-id/messages")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_health_returns_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
