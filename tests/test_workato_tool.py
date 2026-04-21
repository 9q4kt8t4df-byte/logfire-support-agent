# tests/test_workato_tool.py
from __future__ import annotations
import pytest
import respx
import httpx
from unittest.mock import patch
from tools.workato_tool import WorkatoTool


def make_tool(sf_url: str = "", tfs_url: str = "", api_key: str = "") -> WorkatoTool:
    with patch.multiple(
        "config",
        WORKATO_WEBHOOK_SF_READ=sf_url,
        WORKATO_WEBHOOK_TFS_WRITE=tfs_url,
        WORKATO_API_KEY=api_key,
    ):
        return WorkatoTool()


SF_URL = "https://workato.example.com/sf-read"
TFS_URL = "https://workato.example.com/tfs-write"
API_KEY = "test-key"

TFS_KWARGS = dict(
    title="Sync failure on tenant-X",
    root_cause="MS throttling — 429 from external connector",
    affected_tenants=["tenant-X"],
    evidence_links=["https://logfire.example.com/trace/abc123"],
    priority="P2",
    linked_sf_case_id="SF-12345",
)


@pytest.mark.asyncio
async def test_read_sf_case_returns_body_when_configured():
    tool = make_tool(sf_url=SF_URL, api_key=API_KEY)
    with respx.mock:
        respx.post(SF_URL).mock(return_value=httpx.Response(200, text='{"subject":"Login failure"}'))
        result = await tool.read_salesforce_case("SF-12345")
    assert "Login failure" in result


@pytest.mark.asyncio
async def test_read_sf_case_sends_api_key_header():
    tool = make_tool(sf_url=SF_URL, api_key=API_KEY)
    with respx.mock:
        route = respx.post(SF_URL).mock(return_value=httpx.Response(200, text="ok"))
        await tool.read_salesforce_case("SF-99")
    assert route.calls[0].request.headers["x-api-key"] == API_KEY


@pytest.mark.asyncio
async def test_read_sf_case_stub_when_not_configured():
    tool = make_tool()
    result = await tool.read_salesforce_case("SF-12345")
    assert "not configured" in result
    assert "SF-12345" in result


@pytest.mark.asyncio
async def test_read_sf_case_http_error_returns_status_code():
    tool = make_tool(sf_url=SF_URL, api_key=API_KEY)
    with respx.mock:
        respx.post(SF_URL).mock(return_value=httpx.Response(404))
        result = await tool.read_salesforce_case("SF-12345")
    assert "404" in result
    assert "Workato error" in result


@pytest.mark.asyncio
async def test_read_sf_case_network_error_returns_message():
    tool = make_tool(sf_url=SF_URL, api_key=API_KEY)
    with respx.mock:
        respx.post(SF_URL).mock(side_effect=httpx.ConnectError("timeout"))
        result = await tool.read_salesforce_case("SF-12345")
    assert "Workato unreachable" in result


@pytest.mark.asyncio
async def test_create_tfs_ticket_returns_body_when_configured():
    tool = make_tool(tfs_url=TFS_URL, api_key=API_KEY)
    with respx.mock:
        respx.post(TFS_URL).mock(return_value=httpx.Response(200, text='{"id":"TFS-99"}'))
        result = await tool.create_tfs_ticket(**TFS_KWARGS)
    assert "TFS-99" in result


@pytest.mark.asyncio
async def test_create_tfs_ticket_sends_structured_payload():
    tool = make_tool(tfs_url=TFS_URL, api_key=API_KEY)
    with respx.mock:
        route = respx.post(TFS_URL).mock(return_value=httpx.Response(200, text="ok"))
        await tool.create_tfs_ticket(**TFS_KWARGS)
    import json
    payload = json.loads(route.calls[0].request.content)
    assert payload["title"] == TFS_KWARGS["title"]
    assert payload["priority"] == "P2"
    assert payload["linked_sf_case_id"] == "SF-12345"
    assert "body" in payload  # structured markdown body field — added in Task 2


@pytest.mark.asyncio
async def test_create_tfs_ticket_stub_when_not_configured():
    tool = make_tool()
    result = await tool.create_tfs_ticket(**TFS_KWARGS)
    assert "not configured" in result
    assert "SF-12345" in result
    assert "P2" in result
    assert "MS throttling" in result


@pytest.mark.asyncio
async def test_create_tfs_ticket_http_error():
    tool = make_tool(tfs_url=TFS_URL, api_key=API_KEY)
    with respx.mock:
        respx.post(TFS_URL).mock(return_value=httpx.Response(500))
        result = await tool.create_tfs_ticket(**TFS_KWARGS)
    assert "500" in result


@pytest.mark.asyncio
async def test_create_tfs_ticket_network_error():
    tool = make_tool(tfs_url=TFS_URL, api_key=API_KEY)
    with respx.mock:
        respx.post(TFS_URL).mock(side_effect=httpx.ConnectError("refused"))
        result = await tool.create_tfs_ticket(**TFS_KWARGS)
    assert "Workato unreachable" in result


@pytest.mark.asyncio
async def test_call_routes_to_read_sf():
    tool = make_tool()
    result = await tool.call("read_salesforce_case", {"case_id": "SF-1"})
    assert "SF-1" in result


@pytest.mark.asyncio
async def test_call_routes_to_create_tfs():
    tool = make_tool()
    result = await tool.call("create_tfs_ticket", TFS_KWARGS)
    assert "not configured" in result


@pytest.mark.asyncio
async def test_call_unknown_tool_returns_error():
    tool = make_tool()
    result = await tool.call("nonexistent_tool", {})
    assert "Unknown tool" in result


def test_as_tools_returns_two_definitions():
    tool = make_tool()
    defs = tool.as_tools()
    names = [d["name"] for d in defs]
    assert "read_salesforce_case" in names
    assert "create_tfs_ticket" in names


def test_as_tools_create_tfs_has_required_fields():
    tool = make_tool()
    tfs_def = next(d for d in tool.as_tools() if d["name"] == "create_tfs_ticket")
    required = tfs_def["input_schema"]["required"]
    for field in ("title", "root_cause", "affected_tenants", "priority", "linked_sf_case_id"):
        assert field in required
