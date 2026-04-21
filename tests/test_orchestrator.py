# tests/test_orchestrator.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from orchestrator.orchestrator import AgentOrchestrator


@pytest.fixture
def orchestrator(tmp_path):
    db_path = f"sqlite:///{tmp_path}/test.db"
    mock_supervisor = AsyncMock()
    mock_supervisor.run = AsyncMock(return_value="Root cause: MS throttling on sync-worker.")
    mock_supervisor.tools_used = ["query_traces", "delegate_to_agent"]
    return AgentOrchestrator(supervisor=mock_supervisor, db_url=db_path)


@pytest.mark.asyncio
async def test_chat_creates_conversation(orchestrator):
    response = await orchestrator.chat(message="Customer Acme has 500 errors")
    assert response.conversation_id is not None
    assert "throttling" in response.response.lower() or len(response.response) > 0


@pytest.mark.asyncio
async def test_chat_continues_existing_conversation(orchestrator):
    first = await orchestrator.chat(message="Check tenant Acme")
    second = await orchestrator.chat(
        message="Can you also check tenant Beta?",
        conversation_id=first.conversation_id,
    )
    assert second.conversation_id == first.conversation_id


@pytest.mark.asyncio
async def test_chat_unknown_conversation_id_raises(orchestrator):
    with pytest.raises(ValueError, match="Conversation not found"):
        await orchestrator.chat(
            message="Follow up",
            conversation_id="nonexistent-id-xyz",
        )


@pytest.mark.asyncio
async def test_get_messages_returns_history(orchestrator):
    response = await orchestrator.chat(message="Check errors for tenant X")
    messages = orchestrator.get_messages(response.conversation_id)
    assert len(messages) >= 2
    assert messages[0].role == "user"
    assert messages[-1].role == "assistant"


@pytest.mark.asyncio
async def test_tools_used_included_in_response(orchestrator):
    response = await orchestrator.chat(message="Investigate")
    assert "query_traces" in response.tools_used
