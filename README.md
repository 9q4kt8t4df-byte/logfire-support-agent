# LogFire Support Agent

A chat-based investigation agent for support engineers. Replaces Grafana dashboards with
plain-language queries against Logfire telemetry. Detects cross-tenant patterns automatically.

## What It Does

- Ask questions about a customer issue in plain English
- Agent investigates Logfire traces, spans, and logs
- Flags if the same issue affects multiple tenant environments (smoke detection)
- Produces a structured escalation summary ready for TFS (via Workato)

## Prerequisites

- Python 3.11+
- `logfire-mcp` CLI installed: `pip install logfire-mcp`
- A Logfire read token (see Logfire token scope below)
- Anthropic API key

## Setup

```bash
# 1. Clone and install
git clone https://github.com/9q4kt8t4df-byte/logfire-support-agent.git
cd logfire-support-agent
pip install -r requirements.txt

# 2. Configure credentials
cp .env.example .env
# Edit .env — set ANTHROPIC_API_KEY and LOGFIRE_TOKEN at minimum

# 3. (Optional) Verify the Logfire MCP connection: see the collapsible block below

# 4. Start the server
uvicorn api.main:app --reload --port 8000
```

<details>
<summary>Connection check for step 3</summary>

Run this with `LOGFIRE_TOKEN` exported in your shell.

```bash
python -c "
import asyncio, os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
async def check():
    p = StdioServerParameters(command='logfire-mcp', args=['--read-token', os.environ['LOGFIRE_TOKEN']])
    async with stdio_client(p) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            tools = await s.list_tools()
            print('Connected. Tools:', [t.name for t in tools.tools])
asyncio.run(check())
"
```

</details>

## Using the Agent

```bash
# Investigate a customer issue
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Customer Acme is getting 500s on /api/sync since 14:00 UTC"}'

# Include a Salesforce case ID
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Investigate case SF-12345", "case_id": "SF-12345"}'

# Continue a conversation
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Check if other tenants are seeing this too", "conversation_id": "<id from previous response>"}'
```

The request body fields are `message` (required), `case_id` and `conversation_id` (both optional).

## Endpoints

- `POST /api/chat` returns `conversation_id`, `response`, `tools_used` and `smoke_alert` (null unless a platform-wide incident was reported). An unknown `conversation_id` returns 404.
- `GET /api/conversations/{conversation_id}/messages` returns the stored messages (`role`, `content`, `created_at`); 404 for an unknown conversation.
- `GET /health` returns `{"status": "ok"}`.

## Logfire token scope

`LOGFIRE_TOKEN` must be a read token with access across **all tenant projects**, not just one. With a project-scoped token, cross-tenant smoke detection will return empty results. The code does not check the token's scope. Generate the token at the organisation level in the Logfire dashboard.

## Notes for moving to another machine

- `logfire-mcp` must be on `PATH` (`pip install logfire-mcp`). The Logfire tool launches it as a subprocess; if the binary is missing, queries return an error message that says so.
- Set the same `.env` variables.
- `api.anthropic.com` must be reachable for the Anthropic SDK; if outbound HTTPS goes through a proxy, allow it there.
- Conversations are stored in a local SQLite file (see below), so they do not move between machines.

## Conversation storage

`orchestrator/conversation.py` defaults to `sqlite:///conversations.db`, a relative path, so `conversations.db` is created in the directory the server is started from. It is in `.gitignore`.

## Optional integrations

Workato webhooks provide Salesforce, TFS and Teams access. All are optional; set them in `.env`. If a webhook URL is empty, the agent returns a "Workato not configured" message instead of failing (for example, ticket text for manual creation).

| Variable | Default | Enables |
|---|---|---|
| `WORKATO_WEBHOOK_SF_READ` | empty | Reading a Salesforce case (`read_salesforce_case`) |
| `WORKATO_WEBHOOK_SF_UPDATE` | empty | Updating a Salesforce case priority (`update_salesforce_case_priority`) |
| `WORKATO_WEBHOOK_TFS_WRITE` | empty | Creating a TFS ticket (`create_tfs_ticket`) |
| `WORKATO_WEBHOOK_TEAMS_NOTIFY` | empty | Teams alert when a platform-wide smoke alert is found |
| `WORKATO_API_KEY` | empty | Sent as the `x-api-key` header on Workato calls |
| `CHAT_BASE_URL` | `http://localhost:8000` | Base of the conversation link included in Teams alerts |

`SMOKE_THRESHOLD` (default `100`, must be an integer) is also optional; it is used in the supervisor's system prompt. `.env.example` lists only the first three Workato variables with the required ones; the others are read by `config.py`.

## Architecture overview

Open `docs/architecture/index.html` in a browser (no server needed) for a visual overview: request flow, agent roles, tool matrix, integrations, data models and escalation flow.

## Logfire reference

- Logfire API docs: https://pydantic.dev/docs/logfire/api/logfire/
- `knowledge/logfire-sdk-reference.md` explains span attributes, error patterns and how instrumentation libraries structure their spans. The investigator agent reads it through the knowledge tool.

## Running tests

```bash
pytest -v
```

`tests/test_workato_tool.py` imports `respx`, which is not listed in `requirements.txt`; run `pip install respx` first. `tests/conftest.py` sets dummy `ANTHROPIC_API_KEY` and `LOGFIRE_TOKEN` values, so no `.env` is needed.

## Repo map

- `api/`: FastAPI app and request/response models
- `orchestrator/`: chat flow and SQLite conversation store
- `agents/`: tool-use loop, supervisor, investigator, smoke detector
- `tools/`: `logfire_tool.py`, `cross_tenant.py`, `knowledge_tool.py`, `workato_tool.py`
- `knowledge/`: known issues, runbooks, Logfire SDK reference
- `docs/architecture/`: HTML architecture overview
- `docs/superpowers/`: design specs and plans from development
- `config.py`: environment variables and agent definitions
