# LogFire Support Agent — Phase 3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** When a smoke-detector investigation confirms a platform-wide incident, automatically alert the on-call engineer in Microsoft Teams (via Workato) and enable SF case escalation to P1 + TFS ticket creation from the chat confirmation.

**Architecture:** The orchestrator detects a confirmed `platform_wide_incident` smoke alert at the end of `chat()` and fires `WorkatoTool.send_teams_alert()` automatically — no LLM decision involved. Two new Workato webhook methods are added to `WorkatoTool`, three new env vars to `config.py`, and the supervisor prompt gains an instruction to call `update_salesforce_case_priority` before creating a TFS ticket on P1 incidents.

**Tech Stack:** Python 3.9+, httpx, respx (tests), pytest-asyncio, FastAPI, Pydantic v2, Anthropic SDK.

---

## File Map

| File | Change |
|---|---|
| `config.py` | Add `WORKATO_WEBHOOK_TEAMS_NOTIFY`, `WORKATO_WEBHOOK_SF_UPDATE`, `CHAT_BASE_URL`; update supervisor prompt |
| `tools/workato_tool.py` | Add `send_teams_alert()`, `update_salesforce_case_priority()`, extend `__init__`, `as_tools()`, `call()` |
| `orchestrator/orchestrator.py` | Add `workato_tool` param; auto-fire Teams alert in `chat()` |
| `api/main.py` | Pass shared `WorkatoTool` instance to `AgentOrchestrator` |
| `tests/test_workato_tool.py` | Update `make_tool()` helper; add 11 new tests |
| `tests/test_orchestrator.py` | Update `orchestrator` fixture; add 3 new tests |
| `tests/test_agents.py` | Add 1 new test for supervisor prompt |

---

### Task 1: Config — new env vars and supervisor prompt

**Files:**
- Modify: `config.py`
- Modify: `tests/test_agents.py`

- [ ] **Step 1: Write the failing test**

Open `tests/test_agents.py`. Append this test after the last existing test:

```python
def test_supervisor_prompt_includes_update_sf_priority_instruction():
    import config
    prompt = config.AGENTS["support-supervisor"]["system_prompt"]
    assert "update_salesforce_case_priority" in prompt
```

- [ ] **Step 2: Run it to confirm it fails**

```bash
cd "/Users/macnas/Code/VS code/LogFire" && python3 -m pytest tests/test_agents.py::test_supervisor_prompt_includes_update_sf_priority_instruction -v
```

Expected: `FAILED — AssertionError`

- [ ] **Step 3: Add the three new env vars and update the supervisor prompt**

Read `config.py` first. Then make two edits:

**Edit A** — add after `WORKATO_API_KEY = os.getenv("WORKATO_API_KEY", "")`:

```python
WORKATO_WEBHOOK_TEAMS_NOTIFY = os.getenv("WORKATO_WEBHOOK_TEAMS_NOTIFY", "")
WORKATO_WEBHOOK_SF_UPDATE = os.getenv("WORKATO_WEBHOOK_SF_UPDATE", "")
CHAT_BASE_URL = os.getenv("CHAT_BASE_URL", "http://localhost:8000")
```

**Edit B** — in the `support-supervisor` system_prompt, find:

```python
            "Before creating a TFS ticket, present the full ticket body to the engineer and ask for confirmation.\n\n"
```

Replace with:

```python
            "Before creating a TFS ticket, present the full ticket body to the engineer and ask for confirmation.\n"
            "When escalating a confirmed platform-wide incident to P1:\n"
            "1. Call update_salesforce_case_priority(case_id, 'P1') to escalate the SF case.\n"
            "2. Then call create_tfs_ticket with all affected tenant IDs.\n"
            "Always extract the case_id from the [Salesforce case_id: ...] prefix in the conversation.\n\n"
```

- [ ] **Step 4: Run the new test to verify it passes**

```bash
cd "/Users/macnas/Code/VS code/LogFire" && python3 -m pytest tests/test_agents.py::test_supervisor_prompt_includes_update_sf_priority_instruction -v
```

Expected: `PASSED`

- [ ] **Step 5: Run the full suite to verify no regressions**

```bash
cd "/Users/macnas/Code/VS code/LogFire" && python3 -m pytest --tb=short -q
```

Expected: 62 passed, 0 failed.

- [ ] **Step 6: Commit**

```bash
cd "/Users/macnas/Code/VS code/LogFire" && git add config.py tests/test_agents.py && git commit -m "$(cat <<'EOF'
feat: add Teams/SF-update env vars and supervisor escalation instructions

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: WorkatoTool — send_teams_alert and update_salesforce_case_priority

**Files:**
- Modify: `tools/workato_tool.py`
- Modify: `tests/test_workato_tool.py`

- [ ] **Step 1: Write all failing tests**

Read `tests/test_workato_tool.py`. The file currently has a `make_tool()` helper at the top that patches 3 config attributes. You will update it and append 11 new tests.

**Update `make_tool()`** — replace the current definition with:

```python
def make_tool(
    sf_url: str = "",
    tfs_url: str = "",
    api_key: str = "",
    teams_url: str = "",
    sf_update_url: str = "",
) -> WorkatoTool:
    with patch.multiple(
        "config",
        WORKATO_WEBHOOK_SF_READ=sf_url,
        WORKATO_WEBHOOK_TFS_WRITE=tfs_url,
        WORKATO_API_KEY=api_key,
        WORKATO_WEBHOOK_TEAMS_NOTIFY=teams_url,
        WORKATO_WEBHOOK_SF_UPDATE=sf_update_url,
    ):
        return WorkatoTool()
```

Add two new URL constants after the existing ones:

```python
TEAMS_URL = "https://workato.example.com/teams-notify"
SF_UPDATE_URL = "https://workato.example.com/sf-update"
```

Add a constants dict for Teams alert kwargs:

```python
TEAMS_KWARGS = dict(
    case_id="SF-12345",
    root_cause="MS throttling — sync-worker connector",
    affected_tenant_count=14,
    affected_tenant_ids=["tenant-a", "tenant-b"],
    earliest_occurrence_utc="2026-04-22T09:14:00Z",
    pattern_confidence="high",
    conversation_url="http://localhost:8000/api/conversations/abc/messages",
)
```

**Append these 11 tests** at the end of the file:

```python
# ── send_teams_alert ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_send_teams_alert_posts_to_webhook():
    tool = make_tool(teams_url=TEAMS_URL, api_key=API_KEY)
    with respx.mock:
        respx.post(TEAMS_URL).mock(return_value=httpx.Response(200, text='{"ok":true}'))
        result = await tool.send_teams_alert(**TEAMS_KWARGS)
    assert "ok" in result


@pytest.mark.asyncio
async def test_send_teams_alert_sends_api_key_header():
    tool = make_tool(teams_url=TEAMS_URL, api_key=API_KEY)
    with respx.mock:
        route = respx.post(TEAMS_URL).mock(return_value=httpx.Response(200, text="ok"))
        await tool.send_teams_alert(**TEAMS_KWARGS)
    assert route.calls[0].request.headers["x-api-key"] == API_KEY


@pytest.mark.asyncio
async def test_send_teams_alert_payload_contains_all_fields():
    tool = make_tool(teams_url=TEAMS_URL, api_key=API_KEY)
    with respx.mock:
        route = respx.post(TEAMS_URL).mock(return_value=httpx.Response(200, text="ok"))
        await tool.send_teams_alert(**TEAMS_KWARGS)
    import json
    payload = json.loads(route.calls[0].request.content)
    assert payload["case_id"] == "SF-12345"
    assert payload["affected_tenant_count"] == 14
    assert payload["pattern_confidence"] == "high"
    assert "conversation_url" in payload


@pytest.mark.asyncio
async def test_send_teams_alert_stub_when_not_configured():
    tool = make_tool()
    result = await tool.send_teams_alert(**TEAMS_KWARGS)
    assert "not configured" in result
    assert "SF-12345" in result
    assert "14" in result


@pytest.mark.asyncio
async def test_send_teams_alert_http_error():
    tool = make_tool(teams_url=TEAMS_URL, api_key=API_KEY)
    with respx.mock:
        respx.post(TEAMS_URL).mock(return_value=httpx.Response(500))
        result = await tool.send_teams_alert(**TEAMS_KWARGS)
    assert "500" in result


@pytest.mark.asyncio
async def test_send_teams_alert_network_error():
    tool = make_tool(teams_url=TEAMS_URL, api_key=API_KEY)
    with respx.mock:
        respx.post(TEAMS_URL).mock(side_effect=httpx.ConnectError("refused"))
        result = await tool.send_teams_alert(**TEAMS_KWARGS)
    assert "Workato unreachable" in result


# ── update_salesforce_case_priority ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_sf_priority_posts_to_webhook():
    tool = make_tool(sf_update_url=SF_UPDATE_URL, api_key=API_KEY)
    with respx.mock:
        respx.post(SF_UPDATE_URL).mock(return_value=httpx.Response(200, text='{"updated":true}'))
        result = await tool.update_salesforce_case_priority("SF-12345", "P1")
    assert "updated" in result


@pytest.mark.asyncio
async def test_update_sf_priority_payload_contains_case_id_and_priority():
    tool = make_tool(sf_update_url=SF_UPDATE_URL, api_key=API_KEY)
    with respx.mock:
        route = respx.post(SF_UPDATE_URL).mock(return_value=httpx.Response(200, text="ok"))
        await tool.update_salesforce_case_priority("SF-12345", "P1")
    import json
    payload = json.loads(route.calls[0].request.content)
    assert payload["case_id"] == "SF-12345"
    assert payload["priority"] == "P1"


@pytest.mark.asyncio
async def test_update_sf_priority_stub_when_not_configured():
    tool = make_tool()
    result = await tool.update_salesforce_case_priority("SF-12345", "P1")
    assert "not configured" in result
    assert "SF-12345" in result
    assert "P1" in result


@pytest.mark.asyncio
async def test_update_sf_priority_http_error():
    tool = make_tool(sf_update_url=SF_UPDATE_URL, api_key=API_KEY)
    with respx.mock:
        respx.post(SF_UPDATE_URL).mock(return_value=httpx.Response(403))
        result = await tool.update_salesforce_case_priority("SF-12345", "P1")
    assert "403" in result


@pytest.mark.asyncio
async def test_update_sf_priority_network_error():
    tool = make_tool(sf_update_url=SF_UPDATE_URL, api_key=API_KEY)
    with respx.mock:
        respx.post(SF_UPDATE_URL).mock(side_effect=httpx.ConnectError("timeout"))
        result = await tool.update_salesforce_case_priority("SF-12345", "P1")
    assert "Workato unreachable" in result
```

- [ ] **Step 2: Run the new tests to verify they fail**

```bash
cd "/Users/macnas/Code/VS code/LogFire" && python3 -m pytest tests/test_workato_tool.py -k "teams_alert or sf_priority" -v 2>&1 | tail -20
```

Expected: all 11 new tests FAIL with `AttributeError` or `TypeError` (methods don't exist yet).

- [ ] **Step 3: Implement both new methods in workato_tool.py**

Read `tools/workato_tool.py`. Apply these three changes:

**Change A** — update `__init__` to load the two new webhook URLs:

```python
    def __init__(self):
        self.sf_read_url = config.WORKATO_WEBHOOK_SF_READ
        self.tfs_write_url = config.WORKATO_WEBHOOK_TFS_WRITE
        self.api_key = config.WORKATO_API_KEY
        self.teams_notify_url = config.WORKATO_WEBHOOK_TEAMS_NOTIFY
        self.sf_update_url = config.WORKATO_WEBHOOK_SF_UPDATE
```

**Change B** — add both new methods after `create_tfs_ticket` and before `as_tools`:

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
    ) -> str:
        if not self.teams_notify_url:
            return (
                f"[Workato not configured — Teams alert NOT sent. Manual notification required.\n"
                f"Case: {case_id} | Tenants: {affected_tenant_count} | Confidence: {pattern_confidence}]"
            )
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.teams_notify_url,
                    json={
                        "case_id": case_id,
                        "root_cause": root_cause,
                        "affected_tenant_count": affected_tenant_count,
                        "affected_tenant_ids": affected_tenant_ids,
                        "earliest_occurrence_utc": earliest_occurrence_utc,
                        "pattern_confidence": pattern_confidence,
                        "conversation_url": conversation_url,
                    },
                    headers={"x-api-key": self.api_key},
                    timeout=30,
                )
                response.raise_for_status()
                return response.text
        except httpx.HTTPStatusError as e:
            return f"[Workato error — HTTP {e.response.status_code}]"
        except httpx.RequestError as e:
            return f"[Workato unreachable — {type(e).__name__}: {e}]"

    async def update_salesforce_case_priority(
        self,
        case_id: str,
        priority: str,
    ) -> str:
        if not self.sf_update_url:
            return (
                f"[Workato not configured — Salesforce case {case_id} NOT updated. "
                f"Please manually set priority to {priority}.]"
            )
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.sf_update_url,
                    json={"case_id": case_id, "priority": priority},
                    headers={"x-api-key": self.api_key},
                    timeout=30,
                )
                response.raise_for_status()
                return response.text
        except httpx.HTTPStatusError as e:
            return f"[Workato error — HTTP {e.response.status_code}]"
        except httpx.RequestError as e:
            return f"[Workato unreachable — {type(e).__name__}: {e}]"
```

**Change C** — extend `as_tools()` to include both new tools. In the `return [...]` list, append after the `create_tfs_ticket` entry:

```python
            {
                "name": "send_teams_alert",
                "description": (
                    "Send a platform-wide incident alert to Microsoft Teams via Workato. "
                    "Call this when smoke-detector confirms a platform_wide_incident. "
                    "The alert notifies the on-call engineer with a link to this conversation."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "case_id": {"type": "string"},
                        "root_cause": {"type": "string"},
                        "affected_tenant_count": {"type": "integer"},
                        "affected_tenant_ids": {"type": "array", "items": {"type": "string"}},
                        "earliest_occurrence_utc": {"type": "string"},
                        "pattern_confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                        "conversation_url": {"type": "string"},
                    },
                    "required": [
                        "case_id", "root_cause", "affected_tenant_count",
                        "affected_tenant_ids", "earliest_occurrence_utc",
                        "pattern_confidence", "conversation_url",
                    ],
                },
            },
            {
                "name": "update_salesforce_case_priority",
                "description": (
                    "Update the priority of a Salesforce support case via Workato. "
                    "Call this when escalating a confirmed platform-wide incident to P1, "
                    "BEFORE calling create_tfs_ticket. "
                    "Extract case_id from the [Salesforce case_id: ...] prefix in the conversation."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "case_id": {"type": "string", "description": "Salesforce case ID, e.g. SF-12345"},
                        "priority": {"type": "string", "enum": ["P1", "P2", "P3", "P4"]},
                    },
                    "required": ["case_id", "priority"],
                },
            },
```

**Change D** — extend `call()` with two new branches before `return f"Unknown tool: {tool_name}"`:

```python
        if tool_name == "send_teams_alert":
            return await self.send_teams_alert(**tool_input)
        if tool_name == "update_salesforce_case_priority":
            return await self.update_salesforce_case_priority(**tool_input)
```

- [ ] **Step 4: Run all WorkatoTool tests**

```bash
cd "/Users/macnas/Code/VS code/LogFire" && python3 -m pytest tests/test_workato_tool.py -v 2>&1 | tail -20
```

Expected: **28 passed** (17 existing + 11 new), 0 failed.

- [ ] **Step 5: Run the full suite**

```bash
cd "/Users/macnas/Code/VS code/LogFire" && python3 -m pytest --tb=short -q
```

Expected: 73 passed, 0 failed.

- [ ] **Step 6: Commit**

```bash
cd "/Users/macnas/Code/VS code/LogFire" && git add tools/workato_tool.py tests/test_workato_tool.py && git commit -m "$(cat <<'EOF'
feat: add send_teams_alert and update_salesforce_case_priority to WorkatoTool

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: Orchestrator auto-fires Teams alert + api/main.py wiring

**Files:**
- Modify: `orchestrator/orchestrator.py`
- Modify: `api/main.py`
- Modify: `tests/test_orchestrator.py`

- [ ] **Step 1: Write the failing tests**

Read `tests/test_orchestrator.py`. Make two changes:

**Change A** — update the `orchestrator` fixture to pass a `mock_workato`:

```python
@pytest.fixture
def orchestrator(tmp_path):
    db_path = f"sqlite:///{tmp_path}/test.db"
    mock_supervisor = AsyncMock()
    mock_supervisor.run = AsyncMock(return_value="Root cause: MS throttling on sync-worker.")
    mock_supervisor.tools_used = ["query_traces", "delegate_to_agent"]
    mock_workato = AsyncMock()
    mock_workato.send_teams_alert = AsyncMock(return_value="[Teams alert sent]")
    return AgentOrchestrator(
        supervisor=mock_supervisor,
        workato_tool=mock_workato,
        db_url=db_path,
    )
```

**Change B** — append these 3 new tests at the end of the file:

```python
@pytest.mark.asyncio
async def test_chat_sends_teams_alert_on_platform_wide_incident(tmp_path):
    smoke_json = (
        '{"alert_type": "platform_wide_incident", '
        '"pattern": "MS throttling — sync-worker", '
        '"affected_tenant_count": 14, '
        '"affected_tenant_ids": ["tenant-a", "tenant-b"], '
        '"earliest_occurrence_utc": "2026-04-22T09:14:00Z", '
        '"pattern_confidence": "high", '
        '"recommended_priority": "P1"}'
    )
    mock_supervisor = AsyncMock()
    mock_supervisor.run = AsyncMock(return_value=f"Platform incident confirmed. {smoke_json}")
    mock_supervisor.tools_used = []
    mock_workato = AsyncMock()
    mock_workato.send_teams_alert = AsyncMock(return_value="[Teams alert sent]")
    orch = AgentOrchestrator(
        supervisor=mock_supervisor,
        workato_tool=mock_workato,
        db_url=f"sqlite:///{tmp_path}/test.db",
    )
    await orch.chat(message="Check tenant X", case_id="SF-99")
    mock_workato.send_teams_alert.assert_called_once()
    call_kwargs = mock_workato.send_teams_alert.call_args.kwargs
    assert call_kwargs["case_id"] == "SF-99"
    assert call_kwargs["affected_tenant_count"] == 14
    assert call_kwargs["pattern_confidence"] == "high"
    assert "/api/conversations/" in call_kwargs["conversation_url"]


@pytest.mark.asyncio
async def test_chat_does_not_send_teams_alert_for_isolated_incident(tmp_path):
    smoke_json = (
        '{"alert_type": "isolated", '
        '"pattern": "auth failure", '
        '"affected_tenant_count": 1, '
        '"affected_tenant_ids": ["tenant-a"], '
        '"earliest_occurrence_utc": "2026-04-22T09:14:00Z", '
        '"pattern_confidence": "low", '
        '"recommended_priority": "P3"}'
    )
    mock_supervisor = AsyncMock()
    mock_supervisor.run = AsyncMock(return_value=f"Isolated issue found. {smoke_json}")
    mock_supervisor.tools_used = []
    mock_workato = AsyncMock()
    mock_workato.send_teams_alert = AsyncMock(return_value="ok")
    orch = AgentOrchestrator(
        supervisor=mock_supervisor,
        workato_tool=mock_workato,
        db_url=f"sqlite:///{tmp_path}/test.db",
    )
    await orch.chat(message="Check tenant X")
    mock_workato.send_teams_alert.assert_not_called()


@pytest.mark.asyncio
async def test_chat_does_not_send_teams_alert_when_no_smoke_alert(tmp_path):
    mock_supervisor = AsyncMock()
    mock_supervisor.run = AsyncMock(return_value="Root cause: config error in tenant Y.")
    mock_supervisor.tools_used = []
    mock_workato = AsyncMock()
    mock_workato.send_teams_alert = AsyncMock(return_value="ok")
    orch = AgentOrchestrator(
        supervisor=mock_supervisor,
        workato_tool=mock_workato,
        db_url=f"sqlite:///{tmp_path}/test.db",
    )
    await orch.chat(message="Investigate tenant Y")
    mock_workato.send_teams_alert.assert_not_called()
```

- [ ] **Step 2: Run the new tests to verify they fail**

```bash
cd "/Users/macnas/Code/VS code/LogFire" && python3 -m pytest tests/test_orchestrator.py -v 2>&1 | tail -20
```

Expected: existing tests FAIL (fixture now passes `workato_tool` which `AgentOrchestrator.__init__` doesn't accept yet); new tests also FAIL.

- [ ] **Step 3: Update orchestrator/orchestrator.py**

Read `orchestrator/orchestrator.py`. Apply two changes:

**Change A** — update `__init__` to accept `workato_tool`:

```python
from __future__ import annotations
import json
from typing import Optional
from pydantic import ValidationError
from api.models import ChatResponse, MessageRecord, SmokeAlert
from orchestrator.conversation import ConversationStore
from agents.supervisor import SupervisorAgent
from tools.workato_tool import WorkatoTool
import config as cfg


class AgentOrchestrator:
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

**Change B** — in `chat()`, add the Teams alert call after `smoke_alert = self._extract_smoke_alert(response_text)`. Replace:

```python
        smoke_alert = self._extract_smoke_alert(response_text)

        return ChatResponse(
```

With:

```python
        smoke_alert = self._extract_smoke_alert(response_text)

        if smoke_alert:
            conversation_url = (
                f"{cfg.CHAT_BASE_URL}/api/conversations/{conv.id}/messages"
            )
            await self.workato.send_teams_alert(
                case_id=case_id or "",
                root_cause=smoke_alert.pattern,
                affected_tenant_count=smoke_alert.affected_tenant_count,
                affected_tenant_ids=smoke_alert.affected_tenant_ids,
                earliest_occurrence_utc=smoke_alert.earliest_occurrence_utc,
                pattern_confidence=smoke_alert.pattern_confidence,
                conversation_url=conversation_url,
            )

        return ChatResponse(
```

- [ ] **Step 4: Update api/main.py**

Read `api/main.py`. In `build_orchestrator()`, find:

```python
    return AgentOrchestrator(supervisor=supervisor)
```

Replace with:

```python
    return AgentOrchestrator(supervisor=supervisor, workato_tool=workato)
```

- [ ] **Step 5: Run orchestrator tests**

```bash
cd "/Users/macnas/Code/VS code/LogFire" && python3 -m pytest tests/test_orchestrator.py -v 2>&1 | tail -15
```

Expected: **10 passed** (7 existing + 3 new), 0 failed.

- [ ] **Step 6: Run the full suite**

```bash
cd "/Users/macnas/Code/VS code/LogFire" && python3 -m pytest --tb=short -q
```

Expected: **76 passed** (73 previous + 3 new), 0 failed.

- [ ] **Step 7: Commit**

```bash
cd "/Users/macnas/Code/VS code/LogFire" && git add orchestrator/orchestrator.py api/main.py tests/test_orchestrator.py && git commit -m "$(cat <<'EOF'
feat: orchestrator auto-fires Teams alert on platform-wide incident

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Self-Review

**Spec coverage:**

| Spec requirement | Task |
|---|---|
| `send_teams_alert()` on WorkatoTool | Task 2 |
| `update_salesforce_case_priority()` on WorkatoTool | Task 2 |
| `WORKATO_WEBHOOK_TEAMS_NOTIFY`, `WORKATO_WEBHOOK_SF_UPDATE`, `CHAT_BASE_URL` in config | Task 1 |
| Supervisor prompt instructs SF case update before TFS ticket | Task 1 |
| Orchestrator auto-fires Teams alert on `platform_wide_incident` | Task 3 |
| `workato_tool` passed to `AgentOrchestrator` from `build_orchestrator()` | Task 3 |
| Graceful degradation on all new Workato paths | Task 2 (stub tests) |
| Tests: 11 WorkatoTool, 3 orchestrator, 1 agent prompt | Tasks 1–3 |

All spec requirements covered.

**Placeholder scan:** No TBD, no "implement later", all code blocks complete.

**Type consistency:**
- `send_teams_alert` signature in Task 2 implementation matches `TEAMS_KWARGS` in tests and the orchestrator call site in Task 3.
- `update_salesforce_case_priority(case_id, priority)` — same two-param signature throughout.
- `SmokeAlert` fields used in Task 3 (`pattern`, `affected_tenant_count`, `affected_tenant_ids`, `earliest_occurrence_utc`, `pattern_confidence`) all exist in `api/models.py`.
- `AgentOrchestrator.__init__` new signature `(supervisor, workato_tool, db_url)` matches fixture update and `build_orchestrator()` change in Task 3.
