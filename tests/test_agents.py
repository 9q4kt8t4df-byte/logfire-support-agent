# tests/test_agents.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import anthropic
from agents.base import BaseAgent


class ConcreteAgent(BaseAgent):
    """Minimal concrete agent for testing base class."""
    pass


@pytest.fixture
def agent():
    agent_config = {
        "system_prompt": "You are a test agent.",
        "model": "claude-sonnet-4-6",
        "temperature": 0.3,
        "max_tokens": 100,
        "delegable_agents": [],
    }
    return ConcreteAgent(agent_id="test-agent", config=agent_config, tools=[])


@pytest.mark.asyncio
async def test_run_returns_text_on_end_turn(agent):
    mock_response = MagicMock()
    mock_response.stop_reason = "end_turn"
    mock_response.content = [MagicMock(type="text", text="Investigation complete.")]

    with patch("agents.base.anthropic.AsyncAnthropic") as MockClient:
        mock_client = AsyncMock()
        MockClient.return_value = mock_client
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        agent.client = mock_client
        result = await agent.run([{"role": "user", "content": "Investigate this"}])

    assert result == "Investigation complete."


@pytest.mark.asyncio
async def test_run_calls_tool_and_continues(agent):
    tool_use_response = MagicMock()
    tool_use_response.stop_reason = "tool_use"
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.name = "fake_tool"
    tool_block.input = {"param": "value"}
    tool_block.id = "tool-call-1"
    tool_use_response.content = [tool_block]

    end_turn_response = MagicMock()
    end_turn_response.stop_reason = "end_turn"
    end_turn_response.content = [MagicMock(type="text", text="Done after tool call.")]

    mock_tool = AsyncMock()
    mock_tool.call = AsyncMock(return_value="tool result data")

    agent.tool_map = {"fake_tool": mock_tool}

    with patch("agents.base.anthropic.AsyncAnthropic"):
        agent.client = AsyncMock()
        agent.client.messages.create = AsyncMock(
            side_effect=[tool_use_response, end_turn_response]
        )
        result = await agent.run([{"role": "user", "content": "Use the tool"}])

    assert result == "Done after tool call."
    mock_tool.call.assert_called_once_with("fake_tool", {"param": "value"})

from agents.investigator import InvestigatorAgent
from agents.smoke_detector import SmokeDetectorAgent


@pytest.fixture
def investigator():
    from tools.logfire_tool import LogfireTool
    from tools.knowledge_tool import KnowledgeTool
    logfire = LogfireTool(token="test-token")
    knowledge = KnowledgeTool(knowledge_dir="knowledge")
    return InvestigatorAgent(logfire_tool=logfire, knowledge_tool=knowledge)


@pytest.fixture
def smoke_detector():
    from tools.logfire_tool import LogfireTool
    from tools.cross_tenant import CrossTenantTool
    logfire = LogfireTool(token="test-token")
    cross_tenant = CrossTenantTool(logfire_tool=logfire)
    return SmokeDetectorAgent(logfire_tool=logfire, cross_tenant_tool=cross_tenant)


@pytest.mark.asyncio
async def test_investigator_has_correct_tools(investigator):
    tool_names = [t["name"] for t in investigator.tool_definitions]
    assert "query_traces" in tool_names
    assert "get_trace_detail" in tool_names
    assert "search_known_issues" in tool_names
    # Workato tools must NOT be present
    assert "create_tfs_ticket" not in tool_names
    assert "delegate_to_agent" not in tool_names


@pytest.mark.asyncio
async def test_smoke_detector_has_correct_tools(smoke_detector):
    tool_names = [t["name"] for t in smoke_detector.tool_definitions]
    assert "find_pattern_across_tenants" in tool_names
    assert "query_traces" in tool_names
    # Must NOT have Workato or delegation tools
    assert "create_tfs_ticket" not in tool_names
    assert "delegate_to_agent" not in tool_names
