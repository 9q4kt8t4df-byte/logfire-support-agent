# LogFire Support Agent — Phase 3 Design Spec

**Date:** 2026-04-22
**Status:** Approved
**Author:** Support Engineering

---

## Goal

Reduce time-to-escalation for platform-wide incidents by automatically alerting the on-call engineer in Microsoft Teams the moment a confirmed cross-tenant pattern is detected during an investigation — and enabling one-click SF case escalation + TFS ticket creation directly from the chat interface.

---

## What Changes (and What Doesn't)

Phase 3 does **not** introduce a background polling process. The trigger is always an active investigation: a support engineer initiates a chat, the smoke-detector confirms a platform-wide incident, and the notification fires automatically as part of that same request.

**No new agents. No new API endpoints. No new files beyond tests.**

---

## New Env Vars

| Variable | Purpose | Degrades if absent |
|---|---|---|
| `WORKATO_WEBHOOK_TEAMS_NOTIFY` | Webhook URL — Workato posts the alert to Teams | Yes — logs warning, skips notification |
| `WORKATO_WEBHOOK_SF_UPDATE` | Webhook URL — Workato updates SF case priority | Yes — stub message returned |
| `CHAT_BASE_URL` | Base URL of this service, e.g. `http://your-agent:8000` | Default: `http://localhost:8000` |

---

## Changes by File

### `tools/workato_tool.py`

Two new methods added to `WorkatoTool`. Both follow the existing graceful-degradation pattern: return a stub message when the webhook URL is empty, catch `HTTPStatusError` and `RequestError` the same way as existing methods.

#### `send_teams_alert`

Posts an incident alert to a Workato webhook, which formats it as a Teams adaptive card in the on-call channel.

```python
async def send_teams_alert(
    self,
    case_id: str,
    root_cause: str,
    affected_tenant_count: int,
    affected_tenant_ids: list,
    earliest_occurrence_utc: str,
    pattern_confidence: str,
    conversation_url: str,
) -> str
```

Payload sent to `WORKATO_WEBHOOK_TEAMS_NOTIFY`:
```json
{
  "case_id": "SF-12345",
  "root_cause": "MS throttling — sync-worker connector",
  "affected_tenant_count": 14,
  "affected_tenant_ids": ["tenant-a", "tenant-b", "..."],
  "earliest_occurrence_utc": "2026-04-22T09:14:00Z",
  "pattern_confidence": "high",
  "conversation_url": "http://your-agent:8000/chat?conv=<uuid>"
}
```

Stub response (when not configured):
```
[Workato not configured — Teams alert NOT sent. Manual notification required.
Case: SF-12345 | Tenants: 14 | Confidence: high]
```

Exposed to agents via `as_tools()` — the supervisor can call it directly if needed, but in normal flow the orchestrator fires it.

#### `update_salesforce_case_priority`

Updates the priority of an existing Salesforce case via Workato.

```python
async def update_salesforce_case_priority(
    self,
    case_id: str,
    priority: str,   # "P1" | "P2" | "P3" | "P4"
) -> str
```

Payload sent to `WORKATO_WEBHOOK_SF_UPDATE`:
```json
{
  "case_id": "SF-12345",
  "priority": "P1"
}
```

Stub response (when not configured):
```
[Workato not configured — Salesforce case SF-12345 NOT updated.
Please manually set priority to P1.]
```

Exposed to the supervisor agent via `as_tools()` — the supervisor calls this when the engineer confirms a P1 escalation.

---

### `config.py`

Three new top-level variables, added after the existing Workato credentials:

```python
WORKATO_WEBHOOK_TEAMS_NOTIFY = os.getenv("WORKATO_WEBHOOK_TEAMS_NOTIFY", "")
WORKATO_WEBHOOK_SF_UPDATE = os.getenv("WORKATO_WEBHOOK_SF_UPDATE", "")
CHAT_BASE_URL = os.getenv("CHAT_BASE_URL", "http://localhost:8000")
```

Supervisor system prompt updated with one new instruction — call `update_salesforce_case_priority` before creating the TFS ticket when escalating a confirmed platform-wide P1 incident:

```
When the engineer confirms escalation of a platform-wide incident:
1. Call update_salesforce_case_priority(case_id, "P1") to escalate the SF case.
2. Then call create_tfs_ticket with all affected tenant IDs and the structured body.
Always extract the case_id from the [Salesforce case_id: ...] prefix in the conversation.
```

---

### `orchestrator/orchestrator.py`

**`AgentOrchestrator.__init__`** gains a `workato_tool: WorkatoTool` parameter:

```python
def __init__(
    self,
    supervisor: SupervisorAgent,
    workato_tool: WorkatoTool,
    db_url: str = "sqlite:///conversations.db",
) -> None:
    self.supervisor = supervisor
    self.workato = workato_tool
    self.store = ConversationStore(db_url=db_url)
```

**`chat()`** — after `_extract_smoke_alert()` returns a `platform_wide_incident`, fire the Teams alert:

```python
smoke_alert = self._extract_smoke_alert(response_text)

if smoke_alert and smoke_alert.alert_type == "platform_wide_incident":
    conversation_url = f"{cfg.CHAT_BASE_URL}/chat?conv={conv.id}"
    await self.workato.send_teams_alert(
        case_id=case_id or "",
        root_cause=smoke_alert.pattern,
        affected_tenant_count=smoke_alert.affected_tenant_count,
        affected_tenant_ids=smoke_alert.affected_tenant_ids,
        earliest_occurrence_utc=smoke_alert.earliest_occurrence_utc,
        pattern_confidence=smoke_alert.pattern_confidence,
        conversation_url=conversation_url,
    )
```

The alert fires once per `chat()` call that produces a confirmed smoke alert. If Workato is not configured, the graceful-degradation stub is returned and logged — the investigation response is unaffected.

---

### `api/main.py`

`build_orchestrator()` passes the same `WorkatoTool` instance to both the supervisor and the orchestrator:

```python
workato = WorkatoTool()
# ...
supervisor = SupervisorAgent(
    logfire_tool=logfire,
    knowledge_tool=knowledge,
    workato_tool=workato,
    sub_agents={...},
)
return AgentOrchestrator(supervisor=supervisor, workato_tool=workato)
```

---

## Full Escalation Flow

```
1. Engineer: POST /api/chat  { message, case_id: "SF-12345" }

2. Supervisor investigates:
   - WorkatoTool.read_salesforce_case("SF-12345")
   - LogfireTool surface scan
   - Delegate → logfire-investigator (deep trace analysis)
   - Delegate → smoke-detector (auto-trigger: external root cause / error_count > SMOKE_THRESHOLD)

3. smoke-detector returns:
   alert_type: "platform_wide_incident", match_count: 14, confidence: "high"

4. Orchestrator calls:
   WorkatoTool.send_teams_alert(case_id, summary, conversation_url)
   → Workato posts Teams adaptive card to #support-incidents channel

5. Engineer receives Teams alert, taps "Open Investigation →"
   → Opens chat conversation at conversation_url

6. Supervisor presents ticket draft:
   "14 tenants affected. Root cause: MS throttling. Create P1 ticket?"

7. Engineer: "yes"

8. Supervisor calls (in order):
   a. WorkatoTool.update_salesforce_case_priority("SF-12345", "P1")
   b. WorkatoTool.create_tfs_ticket(title, root_cause, affected_tenants, ...)

9. TFS URL returned in chat. SF-12345 is now P1.
```

---

## Teams Notification Payload

The orchestrator sends this JSON to Workato. Workato owns the Teams card formatting.

| Field | Source |
|---|---|
| `case_id` | From `chat()` parameter, same one prepended to conversation |
| `root_cause` | `SmokeAlert.pattern` |
| `affected_tenant_count` | `SmokeAlert.affected_tenant_count` |
| `affected_tenant_ids` | `SmokeAlert.affected_tenant_ids` |
| `earliest_occurrence_utc` | `SmokeAlert.earliest_occurrence_utc` |
| `pattern_confidence` | `SmokeAlert.pattern_confidence` |
| `conversation_url` | `CHAT_BASE_URL + "/chat?conv=" + conversation_id` |

---

## Graceful Degradation

All three new Workato paths degrade independently:

| Webhook missing | Behaviour |
|---|---|
| `WORKATO_WEBHOOK_TEAMS_NOTIFY` | Teams alert skipped — investigation response returned normally |
| `WORKATO_WEBHOOK_SF_UPDATE` | Supervisor returns stub asking engineer to update SF case manually |
| `CHAT_BASE_URL` not set | Defaults to `http://localhost:8000` — link works on local/VDI but not in production without setting this |

---

## Tests

### `tests/test_workato_tool.py` — new tests

- `test_send_teams_alert_posts_to_webhook` — mock 200, verify payload fields
- `test_send_teams_alert_sends_api_key_header`
- `test_send_teams_alert_stub_when_not_configured` — verify case_id and tenant count in stub
- `test_send_teams_alert_http_error` — 500 → "Workato error"
- `test_send_teams_alert_network_error` — ConnectError → "Workato unreachable"
- `test_update_sf_priority_posts_to_webhook` — mock 200, verify case_id and priority in payload
- `test_update_sf_priority_stub_when_not_configured` — verify case_id in stub
- `test_update_sf_priority_http_error`
- `test_update_sf_priority_network_error`
- `test_as_tools_includes_send_teams_alert`
- `test_as_tools_includes_update_salesforce_case_priority`

### `tests/test_orchestrator.py` — new tests

- `test_chat_sends_teams_alert_on_platform_wide_incident` — mock supervisor returning a smoke alert JSON, mock workato, assert `send_teams_alert` called with correct args
- `test_chat_does_not_send_teams_alert_for_isolated_incident` — smoke alert with `alert_type: "isolated"`, assert `send_teams_alert` NOT called
- `test_chat_does_not_send_teams_alert_when_no_smoke_alert` — normal response, assert not called

### `tests/test_agents.py` — new test

- `test_supervisor_prompt_includes_update_sf_priority_instruction` — assert `update_salesforce_case_priority` appears in supervisor system prompt

---

## Credentials Summary

```
# Required for Phase 3
WORKATO_WEBHOOK_TEAMS_NOTIFY=https://workato.example.com/teams-notify
WORKATO_WEBHOOK_SF_UPDATE=https://workato.example.com/sf-update
CHAT_BASE_URL=http://your-agent-host:8000
```

All three degrade gracefully if absent — Phase 1/2 functionality is unaffected.
