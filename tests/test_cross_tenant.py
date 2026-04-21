# tests/test_cross_tenant.py
import pytest
from unittest.mock import AsyncMock, patch
from tools.cross_tenant import CrossTenantTool


@pytest.fixture
def tool():
    from tools.logfire_tool import LogfireTool
    logfire = LogfireTool(token="test-token")
    return CrossTenantTool(logfire_tool=logfire)


@pytest.mark.asyncio
async def test_find_pattern_returns_matches(tool):
    mock_result = '[{"tenant_id": "t1"}, {"tenant_id": "t2"}, {"tenant_id": "t1"}]'
    with patch.object(tool.logfire_tool, "_call_mcp", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = mock_result
        result = await tool.find_pattern_across_tenants(
            error_signature="ThrottlingException",
            service="sync-worker",
            start_utc="2026-04-21T13:00:00Z",
            end_utc="2026-04-21T15:00:00Z",
        )
        assert "t1" in result
        assert "t2" in result
        assert mock_call.called


@pytest.mark.asyncio
async def test_find_pattern_empty_returns_no_matches(tool):
    with patch.object(tool.logfire_tool, "_call_mcp", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = "[]"
        result = await tool.find_pattern_across_tenants(
            error_signature="SomeRareError",
            service="auth-service",
            start_utc="2026-04-21T13:00:00Z",
            end_utc="2026-04-21T14:00:00Z",
        )
        assert "0" in result or "no match" in result.lower()


@pytest.mark.asyncio
async def test_call_dispatch(tool):
    with patch.object(tool, "find_pattern_across_tenants", new_callable=AsyncMock) as mock_fpa:
        mock_fpa.return_value = '{"match_count": 0}'
        result = await tool.call(
            "find_pattern_across_tenants",
            {
                "error_signature": "err",
                "service": "svc",
                "start_utc": "2026-04-21T13:00:00Z",
                "end_utc": "2026-04-21T14:00:00Z",
            },
        )
        assert mock_fpa.called
