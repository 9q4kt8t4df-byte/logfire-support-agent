# tests/test_logfire_tool.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from tools.logfire_tool import LogfireTool


@pytest.fixture
def mock_session():
    session = AsyncMock()
    mock_result = MagicMock()
    mock_result.content = [MagicMock(text='[{"trace_id": "abc123", "service_name": "sync-worker", "is_exception": true}]')]
    session.call_tool = AsyncMock(return_value=mock_result)
    return session


@pytest.fixture
def tool():
    return LogfireTool(token="test-token")


@pytest.mark.asyncio
async def test_query_traces_calls_mcp(tool, mock_session):
    with patch.object(tool, "_call_mcp", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = '[{"trace_id": "abc123"}]'
        result = await tool.query_traces(
            tenant_id="tenant-acme",
            start_utc="2026-04-21T14:00:00Z",
            end_utc="2026-04-21T15:00:00Z",
            error_only=True,
        )
        assert mock_call.called
        assert "abc123" in result


@pytest.mark.asyncio
async def test_get_service_error_rate_calls_mcp(tool):
    with patch.object(tool, "_call_mcp", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = '[{"minute": "14:00", "error_count": 42}]'
        result = await tool.get_service_error_rate(
            tenant_id="tenant-acme",
            service="sync-worker",
            start_utc="2026-04-21T14:00:00Z",
            end_utc="2026-04-21T15:00:00Z",
        )
        assert mock_call.called
        assert "42" in result


@pytest.mark.asyncio
async def test_get_trace_detail_calls_mcp(tool):
    with patch.object(tool, "_call_mcp", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = '[{"span_id": "span1", "parent_span_id": null}]'
        result = await tool.get_trace_detail(trace_id="abc123")
        assert mock_call.called
        assert "span1" in result


@pytest.mark.asyncio
async def test_call_dispatch_query_traces(tool):
    with patch.object(tool, "query_traces", new_callable=AsyncMock) as mock_qt:
        mock_qt.return_value = "[]"
        result = await tool.call(
            "query_traces",
            {"tenant_id": "t1", "start_utc": "2026-04-21T14:00:00Z", "end_utc": "2026-04-21T15:00:00Z"},
        )
        assert mock_qt.called
