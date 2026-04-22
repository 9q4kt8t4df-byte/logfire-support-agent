# tests/test_agents.py
from pathlib import Path
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import anthropic
from agents.base import BaseAgent
from agents.investigator import InvestigatorAgent
from agents.smoke_detector import SmokeDetectorAgent
from agents.supervisor import SupervisorAgent

_KNOWLEDGE_DIR = str(Path(__file__).parent.parent / "knowledge")


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


@pytest.fixture
def investigator():
    from tools.logfire_tool import LogfireTool
    from tools.knowledge_tool import KnowledgeTool
    logfire = LogfireTool(token="test-token")
    knowledge = KnowledgeTool(knowledge_dir=_KNOWLEDGE_DIR)
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


@pytest.fixture
def supervisor():
    from tools.logfire_tool import LogfireTool
    from tools.knowledge_tool import KnowledgeTool
    from tools.workato_tool import WorkatoTool
    from agents.investigator import InvestigatorAgent
    from agents.smoke_detector import SmokeDetectorAgent
    from tools.cross_tenant import CrossTenantTool

    logfire = LogfireTool(token="test-token")
    knowledge = KnowledgeTool(knowledge_dir=_KNOWLEDGE_DIR)
    workato = WorkatoTool()
    cross_tenant = CrossTenantTool(logfire_tool=logfire)
    investigator = InvestigatorAgent(logfire_tool=logfire, knowledge_tool=knowledge)
    smoke_det = SmokeDetectorAgent(logfire_tool=logfire, cross_tenant_tool=cross_tenant)

    return SupervisorAgent(
        logfire_tool=logfire,
        knowledge_tool=knowledge,
        workato_tool=workato,
        sub_agents={"logfire-investigator": investigator, "smoke-detector": smoke_det},
    )


@pytest.mark.asyncio
async def test_supervisor_has_delegate_tool(supervisor):
    tool_names = [t["name"] for t in supervisor.tool_definitions]
    assert "delegate_to_agent" in tool_names


@pytest.mark.asyncio
async def test_supervisor_has_workato_tools(supervisor):
    tool_names = [t["name"] for t in supervisor.tool_definitions]
    assert "read_salesforce_case" in tool_names
    assert "create_tfs_ticket" in tool_names


@pytest.mark.asyncio
async def test_supervisor_delegation_calls_sub_agent(supervisor):
    mock_investigator = AsyncMock()
    mock_investigator.run = AsyncMock(return_value='{"root_cause": "MS throttling"}')
    mock_investigator.tools_used = ["query_traces"]
    supervisor.sub_agents["logfire-investigator"] = mock_investigator

    result = await supervisor._delegate("logfire-investigator", "investigate tenant-acme errors")

    mock_investigator.run.assert_called_once()
    assert "throttling" in result


@pytest.mark.asyncio
async def test_supervisor_delegation_rejects_unknown_agent(supervisor):
    result = await supervisor._delegate("unknown-agent", "some task")
    assert "not found" in result.lower() or "unknown" in result.lower()


def test_smoke_threshold_appears_in_supervisor_prompt():
    """SMOKE_THRESHOLD from config is injected into the supervisor system prompt."""
    import config
    threshold_str = str(config.SMOKE_THRESHOLD)
    prompt = config.AGENTS["support-supervisor"]["system_prompt"]
    assert threshold_str in prompt, (
        f"SMOKE_THRESHOLD ({threshold_str}) not found in supervisor system_prompt. "
        "Did you forget to inject it with an f-string?"
    )


def test_smoke_threshold_invalid_env_raises_clear_error():
    import config
    with pytest.raises(ValueError, match="SMOKE_THRESHOLD must be an integer"):
        config._parse_smoke_threshold("not-a-number")


def test_supervisor_prompt_includes_update_sf_priority_instruction():
    import config
    prompt = config.AGENTS["support-supervisor"]["system_prompt"]
    assert "update_salesforce_case_priority" in prompt
