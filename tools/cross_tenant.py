# tools/cross_tenant.py
from __future__ import annotations
import json
from tools.logfire_tool import LogfireTool


class CrossTenantTool:
    """Queries Logfire across all tenant environments to detect platform-wide patterns."""

    def __init__(self, logfire_tool: LogfireTool):
        self.logfire_tool = logfire_tool

    async def find_pattern_across_tenants(
        self,
        error_signature: str,
        service: str,
        start_utc: str,
        end_utc: str,
    ) -> str:
        """
        Search for an error signature across ALL tenant projects.
        Returns match count, distinct tenant IDs, and earliest occurrence.
        """
        LogfireTool._sanitize(error_signature)
        LogfireTool._sanitize(service)
        LogfireTool._validate_timestamp(start_utc)
        LogfireTool._validate_timestamp(end_utc)
        sql = f"""
            SELECT
                attributes->>'tenant_id' AS tenant_id,
                min(start_timestamp) AS earliest_occurrence,
                count(*) AS error_count
            FROM records
            WHERE start_timestamp >= '{start_utc}'
              AND start_timestamp <= '{end_utc}'
              AND service_name = '{service}'
              AND is_exception = true
              AND (
                exception_message ILIKE '%{error_signature}%'
                OR exception_type ILIKE '%{error_signature}%'
              )
            GROUP BY tenant_id
            ORDER BY earliest_occurrence
        """
        raw = await self.logfire_tool._call_mcp(sql)
        try:
            rows = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            return raw
        if not rows:
            return f"0 tenants affected — no matches found for pattern: {error_signature}"
        tenant_ids = [r["tenant_id"] for r in rows if r.get("tenant_id")]
        earliest = min((r["earliest_occurrence"] for r in rows if r.get("earliest_occurrence")), default="unknown")
        return json.dumps({
            "affected_tenant_count": len(tenant_ids),
            "affected_tenant_ids": tenant_ids,
            "earliest_occurrence_utc": earliest,
            "pattern_confidence": "high" if len(tenant_ids) > 3 else "medium" if len(tenant_ids) > 1 else "low",
        })

    def as_tools(self) -> list:
        return [
            {
                "name": "find_pattern_across_tenants",
                "description": (
                    "Search for an error pattern across ALL tenant environments in Logfire. "
                    "Use this to determine if an issue is isolated to one customer or platform-wide. "
                    "Returns the count of affected tenants, their IDs, and the earliest occurrence time."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "error_signature": {
                            "type": "string",
                            "description": "The normalised error type or message fragment to search for (strip tenant-specific IDs first)",
                        },
                        "service": {
                            "type": "string",
                            "description": "The service name where the error was observed",
                        },
                        "start_utc": {"type": "string", "description": "Start of search window in ISO 8601 UTC"},
                        "end_utc": {"type": "string", "description": "End of search window in ISO 8601 UTC"},
                    },
                    "required": ["error_signature", "service", "start_utc", "end_utc"],
                },
            }
        ]

    async def call(self, tool_name: str, tool_input: dict) -> str:
        if tool_name == "find_pattern_across_tenants":
            return await self.find_pattern_across_tenants(**tool_input)
        return f"Unknown tool: {tool_name}"
