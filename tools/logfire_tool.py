# tools/logfire_tool.py
# mcp is imported inside _call_mcp() only to allow import of this module when mcp is not installed
from __future__ import annotations
import re
from typing import Optional

_ISO_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$")


class LogfireTool:
    """Wraps the Logfire MCP server. All Logfire queries go through this class."""

    MCP_TOOL_NAME = "execute_query"

    def __init__(self, token: str):
        self.token = token

    @staticmethod
    def _sanitize(value: str) -> str:
        """Reject values containing SQL metacharacters to prevent injection."""
        for c in ("'", '"', ";", "--", "/*", "*/", "\\", "\n", "\r"):
            if c in value:
                raise ValueError(f"Invalid characters in query parameter: {value!r}")
        return value

    @staticmethod
    def _validate_timestamp(value: str) -> str:
        if not _ISO_UTC_RE.match(value):
            raise ValueError(f"Invalid timestamp format (expected ISO 8601 UTC): {value!r}")
        return value

    async def _call_mcp(self, sql: str) -> str:
        """Open a fresh MCP connection, execute SQL, return result as string."""
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        import os
        server_params = StdioServerParameters(
            command="logfire-mcp",
            env={**os.environ, "LOGFIRE_TOKEN": self.token},
        )
        try:
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool(
                        self.MCP_TOOL_NAME,
                        {"sql": sql},
                    )
                    if result.content:
                        return result.content[0].text
                    return "[]"
        except FileNotFoundError:
            return "[Error: logfire-mcp binary not found on PATH. Run: pip install logfire-mcp]"

    async def query_traces(
        self,
        tenant_id: str,
        start_utc: str,
        end_utc: str,
        service: Optional[str] = None,
        error_only: bool = False,
    ) -> str:
        """Return spans for a tenant in a time window."""
        self._sanitize(tenant_id)
        self._validate_timestamp(start_utc)
        self._validate_timestamp(end_utc)
        if service:
            self._sanitize(service)
        service_filter = f"AND service_name = '{service}'" if service else ""
        error_filter = "AND is_exception = true" if error_only else ""
        sql = f"""
            SELECT trace_id, span_id, service_name, span_name,
                   start_timestamp, duration_ms, is_exception,
                   exception_type, exception_message, http_status_code
            FROM records
            WHERE attributes->>'tenant_id' = '{tenant_id}'
              AND start_timestamp >= '{start_utc}'
              AND start_timestamp <= '{end_utc}'
              {service_filter}
              {error_filter}
            ORDER BY start_timestamp DESC
            LIMIT 100
        """
        return await self._call_mcp(sql)

    async def get_trace_detail(self, trace_id: str) -> str:
        """Return the full span tree for a single trace."""
        self._sanitize(trace_id)
        sql = f"""
            SELECT span_id, parent_span_id, service_name, span_name,
                   start_timestamp, end_timestamp, duration_ms,
                   is_exception, exception_type, exception_message,
                   http_status_code, attributes
            FROM records
            WHERE trace_id = '{trace_id}'
            ORDER BY start_timestamp
        """
        return await self._call_mcp(sql)

    async def query_logs(self, tenant_id: str, query: str, start_utc: str, end_utc: str) -> str:
        """Structured log search for a tenant."""
        self._sanitize(tenant_id)
        self._sanitize(query)
        self._validate_timestamp(start_utc)
        self._validate_timestamp(end_utc)
        sql = f"""
            SELECT trace_id, span_id, service_name, message,
                   start_timestamp, level
            FROM records
            WHERE attributes->>'tenant_id' = '{tenant_id}'
              AND start_timestamp >= '{start_utc}'
              AND start_timestamp <= '{end_utc}'
              AND (message ILIKE '%{query}%' OR exception_message ILIKE '%{query}%')
            ORDER BY start_timestamp DESC
            LIMIT 50
        """
        return await self._call_mcp(sql)

    async def get_service_error_rate(
        self, tenant_id: str, service: str, start_utc: str, end_utc: str
    ) -> str:
        """Error rate per minute for a service in a time window."""
        self._sanitize(tenant_id)
        self._sanitize(service)
        self._validate_timestamp(start_utc)
        self._validate_timestamp(end_utc)
        sql = f"""
            SELECT
                date_trunc('minute', start_timestamp) AS minute,
                count(*) AS total_spans,
                sum(CASE WHEN is_exception THEN 1 ELSE 0 END) AS error_count
            FROM records
            WHERE attributes->>'tenant_id' = '{tenant_id}'
              AND service_name = '{service}'
              AND start_timestamp >= '{start_utc}'
              AND start_timestamp <= '{end_utc}'
            GROUP BY minute
            ORDER BY minute
        """
        return await self._call_mcp(sql)

    def as_tools(self) -> list[dict]:
        """Return Anthropic tool definitions for this tool."""
        return [
            {
                "name": "query_traces",
                "description": (
                    "Query Logfire spans/traces for a specific tenant and time window. "
                    "Use error_only=true to filter to error spans only. "
                    "Returns up to 100 spans with trace_id, service, error details."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "tenant_id": {"type": "string", "description": "The tenant identifier in Logfire"},
                        "start_utc": {"type": "string", "description": "Start of time window in ISO 8601 UTC"},
                        "end_utc": {"type": "string", "description": "End of time window in ISO 8601 UTC"},
                        "service": {"type": "string", "description": "Filter to a specific service name (optional)"},
                        "error_only": {"type": "boolean", "description": "If true, return only error/exception spans"},
                    },
                    "required": ["tenant_id", "start_utc", "end_utc"],
                },
            },
            {
                "name": "get_trace_detail",
                "description": "Get the complete span tree for a single trace ID. Use this to understand the full call chain for a specific error.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "trace_id": {"type": "string", "description": "The trace ID to inspect"}
                    },
                    "required": ["trace_id"],
                },
            },
            {
                "name": "query_logs",
                "description": "Search log messages for a tenant matching a keyword or error string.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "tenant_id": {"type": "string"},
                        "query": {"type": "string", "description": "Keyword to search in log messages"},
                        "start_utc": {"type": "string"},
                        "end_utc": {"type": "string"},
                    },
                    "required": ["tenant_id", "query", "start_utc", "end_utc"],
                },
            },
            {
                "name": "get_service_error_rate",
                "description": "Get error rate per minute for a service. Use this for a quick surface scan to confirm there is a spike before deep investigation.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "tenant_id": {"type": "string"},
                        "service": {"type": "string"},
                        "start_utc": {"type": "string"},
                        "end_utc": {"type": "string"},
                    },
                    "required": ["tenant_id", "service", "start_utc", "end_utc"],
                },
            },
        ]

    async def call(self, tool_name: str, tool_input: dict) -> str:
        """Dispatch a tool call by name."""
        if tool_name == "query_traces":
            return await self.query_traces(**tool_input)
        if tool_name == "get_trace_detail":
            return await self.get_trace_detail(**tool_input)
        if tool_name == "query_logs":
            return await self.query_logs(**tool_input)
        if tool_name == "get_service_error_rate":
            return await self.get_service_error_rate(**tool_input)
        return f"Unknown tool: {tool_name}"
