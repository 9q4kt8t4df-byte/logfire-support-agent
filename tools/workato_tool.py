# tools/workato_tool.py
import httpx
import config


class WorkatoTool:
    """
    Calls Workato webhook endpoints. The only path to Salesforce and Azure TFS.
    All functions degrade gracefully when webhooks are not configured.
    """

    def __init__(self):
        self.sf_read_url = config.WORKATO_WEBHOOK_SF_READ
        self.tfs_write_url = config.WORKATO_WEBHOOK_TFS_WRITE
        self.api_key = config.WORKATO_API_KEY

    async def read_salesforce_case(self, case_id: str) -> str:
        if not self.sf_read_url:
            return f"[Workato not configured — Salesforce read unavailable. Case ID: {case_id}]"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.sf_read_url,
                    json={"case_id": case_id},
                    headers={"x-api-key": self.api_key},
                    timeout=30,
                )
                response.raise_for_status()
                return response.text
        except httpx.HTTPStatusError as e:
            return f"[Workato error — HTTP {e.response.status_code}: {e.response.text[:200]}]"
        except httpx.RequestError as e:
            return f"[Workato unreachable — {type(e).__name__}: {e}]"

    async def create_tfs_ticket(
        self,
        title: str,
        root_cause: str,
        affected_tenants: list,
        evidence_links: list,
        priority: str,
        linked_sf_case_id: str,
    ) -> str:
        if not self.tfs_write_url:
            return (
                "[Workato not configured — TFS ticket NOT created. "
                "Please create manually with the following details:\n"
                f"Title: {title}\n"
                f"Priority: {priority}\n"
                f"SF Case: {linked_sf_case_id}\n"
                f"Root Cause: {root_cause}\n"
                f"Affected Tenants: {', '.join(affected_tenants)}\n"
                f"Evidence: {', '.join(evidence_links)}]"
            )
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.tfs_write_url,
                    json={
                        "title": title,
                        "root_cause": root_cause,
                        "affected_tenants": affected_tenants,
                        "evidence_links": evidence_links,
                        "priority": priority,
                        "linked_sf_case_id": linked_sf_case_id,
                    },
                    headers={"x-api-key": self.api_key},
                    timeout=30,
                )
                response.raise_for_status()
                return response.text
        except httpx.HTTPStatusError as e:
            return f"[Workato error — HTTP {e.response.status_code}: {e.response.text[:200]}]"
        except httpx.RequestError as e:
            return f"[Workato unreachable — {type(e).__name__}: {e}]"

    def as_tools(self) -> list:
        return [
            {
                "name": "read_salesforce_case",
                "description": (
                    "Fetch details of a Salesforce support case by case ID. "
                    "Returns case subject, description, customer name, tenant_id, priority, and opened_at. "
                    "Call this first if the engineer provides a case_id."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "case_id": {"type": "string", "description": "Salesforce case ID, e.g. SF-12345"}
                    },
                    "required": ["case_id"],
                },
            },
            {
                "name": "create_tfs_ticket",
                "description": (
                    "Create an escalation ticket in Azure TFS/Azure DevOps. "
                    "IMPORTANT: Always present the ticket body to the engineer and receive confirmation BEFORE calling this tool."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "root_cause": {"type": "string"},
                        "affected_tenants": {"type": "array", "items": {"type": "string"}},
                        "evidence_links": {"type": "array", "items": {"type": "string"}},
                        "priority": {"type": "string", "enum": ["P1", "P2", "P3", "P4"]},
                        "linked_sf_case_id": {"type": "string"},
                    },
                    "required": ["title", "root_cause", "affected_tenants", "evidence_links", "priority", "linked_sf_case_id"],
                },
            },
        ]

    async def call(self, tool_name: str, tool_input: dict) -> str:
        if tool_name == "read_salesforce_case":
            return await self.read_salesforce_case(**tool_input)
        if tool_name == "create_tfs_ticket":
            return await self.create_tfs_ticket(**tool_input)
        return f"Unknown tool: {tool_name}"
