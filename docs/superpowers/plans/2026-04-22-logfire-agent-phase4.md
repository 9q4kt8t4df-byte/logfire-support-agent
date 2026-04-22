# LogFire Support Agent — Phase 4 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a single static HTML file (`docs/architecture/index.html`) that explains the LogFire Support Agent architecture to both technical and non-technical readers, using Mermaid.js diagrams and a sidebar + tab layout.

**Architecture:** One self-contained HTML file with embedded CSS, JS, and Mermaid diagram definitions. Mermaid.js loads from CDN. No build step, no server — open by double-clicking in any browser.

**Tech Stack:** HTML5, CSS3, vanilla JS, Mermaid.js 10 (CDN: `cdn.jsdelivr.net/npm/mermaid@10`).

---

## File Map

| File | Change |
|---|---|
| `docs/architecture/index.html` | Create — complete documentation site |
| `.gitignore` | Modify — add `.superpowers/` entry |

---

### Task 1: Create `docs/architecture/index.html` — complete static documentation site

**Files:**
- Create: `docs/architecture/index.html`
- Modify: `.gitignore`

There are no automated tests for a static HTML file. Verification is a manual checklist run in the browser.

- [ ] **Step 1: Create the directory**

```bash
mkdir -p "/Users/macnas/Code/VS code/LogFire/docs/architecture"
```

- [ ] **Step 2: Write the complete file**

Create `/Users/macnas/Code/VS code/LogFire/docs/architecture/index.html` with the following content (write the entire file in one operation):

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LogFire Support Agent — Architecture</title>
<script type="module">
  import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
  mermaid.initialize({ startOnLoad: true, theme: 'dark' });
</script>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { height: 100%; }
body { background: #0d0d0d; color: #ccc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; font-size: 14px; }
.page { display: flex; height: 100vh; overflow: hidden; }

.sidebar { width: 200px; background: #080808; border-right: 1px solid #1a1a1a; display: flex; flex-direction: column; flex-shrink: 0; overflow-y: auto; }
.sidebar-brand { padding: 16px; border-bottom: 1px solid #1a1a1a; }
.sidebar-brand-name { color: #fff; font-weight: 700; font-size: 0.9em; }
.sidebar-brand-sub { color: #555; font-size: 0.72em; margin-top: 2px; }
.nav-item { padding: 9px 16px; color: #555; cursor: pointer; font-size: 0.82em; border-left: 2px solid transparent; transition: color 0.1s, background 0.1s; user-select: none; }
.nav-item:hover { color: #aaa; background: rgba(255,255,255,0.03); }
.nav-item.active { background: rgba(74,160,100,0.12); border-left-color: #4a9; color: #4a9; font-weight: 600; }
.sidebar-footer { margin-top: auto; padding: 12px 16px; border-top: 1px solid #1a1a1a; color: #444; font-size: 0.72em; line-height: 1.6; }

.main { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
.section-panel { display: none; flex-direction: column; height: 100%; }
.section-panel.active { display: flex; }
.section-header { padding: 18px 24px 14px; border-bottom: 1px solid #1a1a1a; flex-shrink: 0; }
.section-title { color: #fff; font-size: 1.05em; font-weight: 700; }
.section-subtitle { color: #555; font-size: 0.78em; margin-top: 3px; }

.tabs { display: flex; border-bottom: 1px solid #1a1a1a; background: #080808; flex-shrink: 0; }
.tab { padding: 9px 20px; color: #555; cursor: pointer; font-size: 0.8em; border-bottom: 2px solid transparent; transition: color 0.15s; user-select: none; }
.tab:hover { color: #aaa; }
.tab.active { color: #4a9; border-bottom-color: #4a9; font-weight: 600; }
.tab-content { flex: 1; overflow-y: auto; padding: 24px; display: none; }
.tab-content.active { display: block; }

.prose { color: #bbb; line-height: 1.75; max-width: 660px; font-size: 0.85em; }
.prose p { margin-bottom: 12px; }
.prose strong { color: #e0e0e0; }
.prose ul { margin: 8px 0 12px 20px; }
.prose li { margin-bottom: 4px; }
.ba-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 16px; max-width: 620px; }
.ba-card { background: #0f1f17; border: 1px solid #1a3a2a; border-radius: 6px; padding: 14px; }
.ba-label { color: #4a9; font-weight: 600; font-size: 0.82em; margin-bottom: 5px; }
.ba-text { color: #666; font-size: 0.78em; line-height: 1.6; }

.diagram-wrap { background: #0a0a0a; border: 1px solid #222; border-radius: 8px; padding: 24px; margin-bottom: 20px; overflow-x: auto; }
.file-refs-label { color: #555; font-size: 0.72em; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px; }
.file-list { display: flex; flex-wrap: wrap; gap: 6px; }
.file-tag { background: #111; border: 1px solid #2a2a2a; border-radius: 4px; padding: 3px 10px; font-family: monospace; font-size: 0.78em; color: #888; }
.file-tag span { color: #4a9; }
.note { background: #111; border-left: 3px solid #4a9; padding: 10px 14px; border-radius: 0 4px 4px 0; font-size: 0.82em; color: #999; margin: 12px 0; max-width: 660px; line-height: 1.6; }
</style>
</head>
<body>
<div class="page">

  <div class="sidebar">
    <div class="sidebar-brand">
      <div class="sidebar-brand-name">LogFire</div>
      <div class="sidebar-brand-sub">Support Agent</div>
    </div>
    <div class="nav-item active" data-nav="overview" onclick="showSection('overview')">System Overview</div>
    <div class="nav-item" data-nav="request-flow" onclick="showSection('request-flow')">Request Flow</div>
    <div class="nav-item" data-nav="agents" onclick="showSection('agents')">Agent Roles</div>
    <div class="nav-item" data-nav="tools" onclick="showSection('tools')">Tool Matrix</div>
    <div class="nav-item" data-nav="integrations" onclick="showSection('integrations')">Integrations</div>
    <div class="nav-item" data-nav="data-models" onclick="showSection('data-models')">Data Models</div>
    <div class="nav-item" data-nav="escalation" onclick="showSection('escalation')">Escalation Flow</div>
    <div class="sidebar-footer">Phase 1–3 complete<br>76 tests passing</div>
  </div>

  <div class="main">

    <!-- 1. SYSTEM OVERVIEW -->
    <div id="section-overview" class="section-panel active">
      <div class="section-header">
        <div class="section-title">System Overview</div>
        <div class="section-subtitle">What this agent is and why it exists</div>
      </div>
      <div class="tabs">
        <div class="tab active" id="overview-tab-what" onclick="switchTab('overview','what')">What it does</div>
        <div class="tab" id="overview-tab-how" onclick="switchTab('overview','how')">How it works</div>
      </div>
      <div id="overview-content-what" class="tab-content active">
        <div class="prose">
          <p>The <strong>LogFire Support Agent</strong> is an AI-powered assistant that helps support engineers investigate customer issues faster — without needing direct database access or manual log analysis.</p>
          <p>When a support case comes in, an engineer sends a message to the agent. The agent reads the Salesforce case, queries Logfire for traces and errors, identifies the root cause, and — if the same error is affecting multiple customers — automatically alerts the on-call engineer in Microsoft Teams.</p>
          <p>The investigation that used to take 30–60 minutes of manual log searching now takes under 2 minutes.</p>
          <div class="ba-grid">
            <div class="ba-card">
              <div class="ba-label">Before</div>
              <div class="ba-text">Engineer manually searches Grafana, Splunk, and Salesforce. 30–60 min to identify root cause. Platform-wide incidents detected late.</div>
            </div>
            <div class="ba-card">
              <div class="ba-label">After</div>
              <div class="ba-text">Agent investigates automatically. Root cause and affected tenants in under 2 min. Platform-wide incidents trigger Teams alerts immediately.</div>
            </div>
          </div>
        </div>
      </div>
      <div id="overview-content-how" class="tab-content">
        <div class="diagram-wrap">
          <pre class="mermaid">
graph TB
    API["FastAPI\n/api/chat"]
    O["AgentOrchestrator\norchestrator.py"]
    S["support-supervisor\nagents/supervisor.py"]
    I["logfire-investigator\nagents/investigator.py"]
    SD["smoke-detector\nagents/smoke_detector.py"]
    T["Tools\nLogfire · Workato · Knowledge"]

    API --> O --> S
    S -->|delegate| I
    S -->|delegate| SD
    S --> T
    I --> T
    SD --> T
          </pre>
        </div>
        <div class="file-refs-label">Key files</div>
        <div class="file-list">
          <div class="file-tag"><span>api/</span>main.py</div>
          <div class="file-tag"><span>orchestrator/</span>orchestrator.py</div>
          <div class="file-tag"><span>agents/</span>supervisor.py</div>
          <div class="file-tag">config.py</div>
        </div>
      </div>
    </div>

    <!-- 2. REQUEST FLOW -->
    <div id="section-request-flow" class="section-panel">
      <div class="section-header">
        <div class="section-title">Request Flow</div>
        <div class="section-subtitle">How a support engineer's message becomes an investigation result</div>
      </div>
      <div class="tabs">
        <div class="tab active" id="request-flow-tab-what" onclick="switchTab('request-flow','what')">What it does</div>
        <div class="tab" id="request-flow-tab-how" onclick="switchTab('request-flow','how')">How it works</div>
      </div>
      <div id="request-flow-content-what" class="tab-content active">
        <div class="prose">
          <p>When an engineer sends a message, the agent reads the relevant Salesforce case, queries Logfire for traces and error patterns, delegates deep investigation to specialist sub-agents, and returns a structured root-cause summary.</p>
          <p>If the investigation reveals the same error pattern across multiple customer tenants, the agent automatically sends an alert to the on-call Microsoft Teams channel — without the engineer needing to do anything extra.</p>
          <div class="ba-grid">
            <div class="ba-card">
              <div class="ba-label">Single-tenant issue</div>
              <div class="ba-text">Supervisor + logfire-investigator. Root cause returned in chat. No Teams alert sent.</div>
            </div>
            <div class="ba-card">
              <div class="ba-label">Platform-wide incident</div>
              <div class="ba-text">Supervisor + investigator + smoke-detector. Teams alert fires automatically. Engineer confirms P1 escalation in chat.</div>
            </div>
          </div>
        </div>
      </div>
      <div id="request-flow-content-how" class="tab-content">
        <div class="diagram-wrap">
          <pre class="mermaid">
sequenceDiagram
    actor E as Engineer
    participant API as FastAPI /api/chat
    participant O as AgentOrchestrator
    participant S as support-supervisor
    participant I as logfire-investigator
    participant SD as smoke-detector
    participant W as WorkatoTool
    participant LF as Logfire

    E->>API: POST /api/chat {message, case_id}
    API->>O: chat(message, case_id)
    O->>O: Load conversation history (SQLite)
    O->>S: run(history)
    S->>W: read_salesforce_case(case_id)
    S->>LF: get_service_error_rate()
    S->>I: delegate(tenant_id, symptom)
    I->>LF: query_traces(), get_trace_detail()
    I-->>S: root cause summary
    S->>SD: delegate(pattern, time_range)
    SD->>LF: cross_tenant_search()
    SD-->>S: platform_wide_incident (14 tenants)
    S-->>O: response text + smoke alert JSON
    O->>W: send_teams_alert(case_id, summary)
    W-->>O: alert sent
    O-->>API: ChatResponse
    API-->>E: {response, conversation_id, smoke_alert}
          </pre>
        </div>
        <div class="file-refs-label">Key files</div>
        <div class="file-list">
          <div class="file-tag"><span>api/</span>main.py</div>
          <div class="file-tag"><span>orchestrator/</span>orchestrator.py</div>
          <div class="file-tag"><span>agents/</span>base.py</div>
          <div class="file-tag"><span>agents/</span>supervisor.py</div>
        </div>
      </div>
    </div>

    <!-- 3. AGENT ROLES -->
    <div id="section-agents" class="section-panel">
      <div class="section-header">
        <div class="section-title">Agent Roles</div>
        <div class="section-subtitle">The three agents, their responsibilities, and delegation boundaries</div>
      </div>
      <div class="tabs">
        <div class="tab active" id="agents-tab-what" onclick="switchTab('agents','what')">What it does</div>
        <div class="tab" id="agents-tab-how" onclick="switchTab('agents','how')">How it works</div>
      </div>
      <div id="agents-content-what" class="tab-content active">
        <div class="prose">
          <p>The system has three agents with distinct roles. The <strong>support-supervisor</strong> is the entry point — it reads the Salesforce case, does a surface scan of Logfire, and decides which specialist agents to call.</p>
          <p>The <strong>logfire-investigator</strong> does a deep dive into a single tenant's traces to find the root cause of a specific error. It has no power to create tickets or send alerts.</p>
          <p>The <strong>smoke-detector</strong> searches across all tenants for the same error pattern. If the same issue affects more than a configurable threshold of tenants, it confirms a platform-wide incident.</p>
          <p>Sub-agents cannot delegate further — this is an intentional safety boundary that prevents runaway agent chains.</p>
        </div>
      </div>
      <div id="agents-content-how" class="tab-content">
        <div class="diagram-wrap">
          <pre class="mermaid">
graph TD
    S["support-supervisor\nCoordinates the full investigation\nAccess: Workato · Logfire · Knowledge · Delegate"]
    I["logfire-investigator\nDeep single-tenant trace analysis\nAccess: Logfire · Knowledge"]
    SD["smoke-detector\nCross-tenant pattern matching\nAccess: Logfire · CrossTenant"]

    S -->|"delegate_to_agent()"| I
    S -->|"delegate_to_agent()"| SD
          </pre>
        </div>
        <div class="note">Sub-agents do not have access to <code>DelegateTool</code> — they cannot spawn further agents. This boundary is enforced in <code>config.py</code> by omitting <code>DelegateTool</code> from their tool lists.</div>
        <div class="file-refs-label">Key files</div>
        <div class="file-list">
          <div class="file-tag"><span>agents/</span>supervisor.py</div>
          <div class="file-tag"><span>agents/</span>investigator.py</div>
          <div class="file-tag"><span>agents/</span>smoke_detector.py</div>
          <div class="file-tag">config.py</div>
        </div>
      </div>
    </div>

    <!-- 4. TOOL MATRIX -->
    <div id="section-tools" class="section-panel">
      <div class="section-header">
        <div class="section-title">Tool Matrix</div>
        <div class="section-subtitle">Which agent can call which tool, and why access is restricted</div>
      </div>
      <div class="tabs">
        <div class="tab active" id="tools-tab-what" onclick="switchTab('tools','what')">What it does</div>
        <div class="tab" id="tools-tab-how" onclick="switchTab('tools','how')">How it works</div>
      </div>
      <div id="tools-content-what" class="tab-content active">
        <div class="prose">
          <p>Each agent has access to exactly the tools it needs — nothing more. This is a deliberate design choice: restricting tool access limits what an agent can do if it makes a wrong decision.</p>
          <p>Only the <strong>support-supervisor</strong> can create TFS tickets, update Salesforce cases, send Teams alerts, or delegate to other agents. Sub-agents can read data but cannot take any write actions.</p>
          <p>The <strong>CrossTenantTool</strong> is only available to the smoke-detector, which is the only agent with a mandate to query across all customer tenants.</p>
        </div>
      </div>
      <div id="tools-content-how" class="tab-content">
        <div class="diagram-wrap">
          <pre class="mermaid">
graph LR
    S[support-supervisor]
    I[logfire-investigator]
    SD[smoke-detector]

    LF["LogfireTool\nTraces · logs · error rates"]
    W["WorkatoTool\nSalesforce · TFS · Teams"]
    K["KnowledgeTool\nRunbooks · known issues"]
    D["DelegateTool\nSub-agent dispatch"]
    CT["CrossTenantTool\nMulti-tenant search"]

    S --> LF
    S --> W
    S --> K
    S --> D
    I --> LF
    I --> K
    SD --> LF
    SD --> CT
          </pre>
        </div>
        <div class="file-refs-label">Key files</div>
        <div class="file-list">
          <div class="file-tag"><span>tools/</span>logfire_tool.py</div>
          <div class="file-tag"><span>tools/</span>workato_tool.py</div>
          <div class="file-tag"><span>tools/</span>knowledge_tool.py</div>
          <div class="file-tag"><span>tools/</span>cross_tenant.py</div>
          <div class="file-tag">config.py</div>
        </div>
      </div>
    </div>

    <!-- 5. INTEGRATIONS -->
    <div id="section-integrations" class="section-panel">
      <div class="section-header">
        <div class="section-title">Integrations</div>
        <div class="section-subtitle">Every external system the agent connects to</div>
      </div>
      <div class="tabs">
        <div class="tab active" id="integrations-tab-what" onclick="switchTab('integrations','what')">What it does</div>
        <div class="tab" id="integrations-tab-how" onclick="switchTab('integrations','how')">How it works</div>
      </div>
      <div id="integrations-content-what" class="tab-content active">
        <div class="prose">
          <p>The agent connects to five external systems. <strong>Logfire</strong> is where all trace and error data lives — the agent reads it to understand what's happening in customer environments. <strong>Workato</strong> is the middleware layer that connects the agent to Salesforce, Azure TFS, and Microsoft Teams.</p>
          <p>Every Workato integration degrades gracefully — if a webhook URL is not configured, the tool returns a plain-text message explaining what was skipped and what the engineer needs to do manually. The investigation continues regardless.</p>
          <p>The only local storage is a <strong>SQLite file</strong> (<code>conversations.db</code>) that stores conversation history so engineers can continue an investigation across multiple messages.</p>
        </div>
      </div>
      <div id="integrations-content-how" class="tab-content">
        <div class="diagram-wrap">
          <pre class="mermaid">
graph TB
    A["LogFire Support Agent"]

    LF["Logfire\nPydantic observability platform"]
    WK["Workato\niPaaS middleware"]
    SF["Salesforce\nsupport cases"]
    TFS["Azure TFS\nengineering tickets"]
    T["Microsoft Teams\non-call alerts"]
    DB["SQLite\nconversations.db"]

    A -->|"MCP server · LOGFIRE_TOKEN"| LF
    A -->|"WORKATO_WEBHOOK_SF_READ\nWORKATO_API_KEY"| WK
    WK -->|"REST API"| SF
    WK -->|"REST API"| TFS
    WK -->|"webhook"| T
    A -->|"local file"| DB
          </pre>
        </div>
        <div class="note">All Workato env vars degrade gracefully if unset: <code>WORKATO_WEBHOOK_SF_READ</code>, <code>WORKATO_WEBHOOK_TFS_WRITE</code>, <code>WORKATO_WEBHOOK_TEAMS_NOTIFY</code>, <code>WORKATO_WEBHOOK_SF_UPDATE</code>, <code>WORKATO_API_KEY</code>.</div>
        <div class="file-refs-label">Key files</div>
        <div class="file-list">
          <div class="file-tag"><span>tools/</span>workato_tool.py</div>
          <div class="file-tag"><span>tools/</span>logfire_tool.py</div>
          <div class="file-tag">config.py</div>
        </div>
      </div>
    </div>

    <!-- 6. DATA MODELS -->
    <div id="section-data-models" class="section-panel">
      <div class="section-header">
        <div class="section-title">Data Models</div>
        <div class="section-subtitle">The key data structures — what goes in, what comes out, what's persisted</div>
      </div>
      <div class="tabs">
        <div class="tab active" id="data-models-tab-what" onclick="switchTab('data-models','what')">What it does</div>
        <div class="tab" id="data-models-tab-how" onclick="switchTab('data-models','how')">How it works</div>
      </div>
      <div id="data-models-content-what" class="tab-content active">
        <div class="prose">
          <p>The API has a simple contract: a <strong>ChatRequest</strong> comes in (message, optional case ID, optional conversation ID) and a <strong>ChatResponse</strong> goes out (response text, conversation ID for follow-ups, tools used, and an optional smoke alert).</p>
          <p>A <strong>SmokeAlert</strong> is only present in the response when the smoke-detector has confirmed a platform-wide incident. It carries the root cause, affected tenant count, and recommended escalation priority.</p>
          <p>Conversation history is persisted in <strong>SQLite</strong> as a parent Conversation record with child Message records. Foreign key constraints are enforced.</p>
        </div>
      </div>
      <div id="data-models-content-how" class="tab-content">
        <div class="diagram-wrap">
          <pre class="mermaid">
erDiagram
    ChatRequest {
        string message
        string case_id
        string conversation_id
    }
    ChatResponse {
        string conversation_id
        string response
        list tools_used
        object smoke_alert
    }
    SmokeAlert {
        string alert_type
        string pattern
        int affected_tenant_count
        list affected_tenant_ids
        string earliest_occurrence_utc
        string pattern_confidence
        string recommended_priority
    }
    Conversation {
        string id PK
        datetime created_at
    }
    Message {
        int id PK
        string conversation_id FK
        string role
        string content
        datetime created_at
    }

    ChatRequest ||--o| ChatResponse : produces
    ChatResponse ||--o| SmokeAlert : contains
    Conversation ||--|{ Message : contains
          </pre>
        </div>
        <div class="file-refs-label">Key files</div>
        <div class="file-list">
          <div class="file-tag"><span>api/</span>models.py</div>
          <div class="file-tag"><span>orchestrator/</span>conversation.py</div>
        </div>
      </div>
    </div>

    <!-- 7. ESCALATION FLOW -->
    <div id="section-escalation" class="section-panel">
      <div class="section-header">
        <div class="section-title">Escalation Flow</div>
        <div class="section-subtitle">Full P1 path: smoke detected → Teams alert → engineer confirms → SF + TFS</div>
      </div>
      <div class="tabs">
        <div class="tab active" id="escalation-tab-what" onclick="switchTab('escalation','what')">What it does</div>
        <div class="tab" id="escalation-tab-how" onclick="switchTab('escalation','how')">How it works</div>
      </div>
      <div id="escalation-content-what" class="tab-content active">
        <div class="prose">
          <p>When the smoke-detector confirms a platform-wide incident, the orchestrator automatically sends a Teams alert to the on-call channel. The alert includes the root cause, number of affected tenants, and a link back to the chat conversation.</p>
          <p>The engineer opens the conversation link, reviews the agent's findings, and types "yes" to confirm P1 escalation. The agent then updates the Salesforce case priority to P1 and creates an Azure TFS engineering ticket — in that order.</p>
          <p><strong>Nothing is automatic after the Teams alert.</strong> The engineer must explicitly confirm before any write actions are taken in Salesforce or TFS.</p>
        </div>
      </div>
      <div id="escalation-content-how" class="tab-content">
        <div class="diagram-wrap">
          <pre class="mermaid">
flowchart TD
    A([Engineer sends message]) --> B[Supervisor investigates]
    B --> C{smoke-detector\nconfirms platform-wide?}
    C -->|No| D([Return root cause to engineer])
    C -->|Yes| E[Orchestrator fires\nsend_teams_alert]
    E --> F([Teams alert to on-call channel\nwith conversation link])
    F --> G[Engineer opens conversation\nreviews findings]
    G --> H{Engineer confirms\nP1 escalation?}
    H -->|No| I([Investigation closed\nno ticket created])
    H -->|Yes| J[Supervisor calls\nupdate_salesforce_case_priority P1]
    J --> K[Supervisor calls\ncreate_tfs_ticket]
    K --> L([TFS URL returned in chat\nSF case now P1])

    style E fill:#1a3a5a,stroke:#4af,color:#9df
    style F fill:#1a3a5a,stroke:#4af,color:#9df
    style J fill:#1a3a2a,stroke:#4a9,color:#9da
    style K fill:#1a3a2a,stroke:#4a9,color:#9da
    style H fill:#2a1a0a,stroke:#c84,color:#da9
          </pre>
        </div>
        <div class="file-refs-label">Key files</div>
        <div class="file-list">
          <div class="file-tag"><span>orchestrator/</span>orchestrator.py</div>
          <div class="file-tag"><span>tools/</span>workato_tool.py</div>
          <div class="file-tag"><span>agents/</span>supervisor.py</div>
        </div>
      </div>
    </div>

  </div><!-- .main -->
</div><!-- .page -->

<script>
function showSection(name) {
  document.querySelectorAll('.section-panel').forEach(function(p) { p.classList.remove('active'); });
  document.querySelectorAll('.nav-item').forEach(function(n) { n.classList.remove('active'); });
  document.getElementById('section-' + name).classList.add('active');
  document.querySelector('[data-nav="' + name + '"]').classList.add('active');
}

function switchTab(section, tab) {
  var prefix = '#section-' + section + ' ';
  document.querySelectorAll(prefix + '.tab').forEach(function(t) { t.classList.remove('active'); });
  document.querySelectorAll(prefix + '.tab-content').forEach(function(c) { c.classList.remove('active'); });
  document.getElementById(section + '-tab-' + tab).classList.add('active');
  document.getElementById(section + '-content-' + tab).classList.add('active');
}
</script>
</body>
</html>
```

- [ ] **Step 3: Open in browser and run the verification checklist**

Open the file:
```bash
open "/Users/macnas/Code/VS code/LogFire/docs/architecture/index.html"
```

Verify all 7 items:
- [ ] Page loads without console errors (open DevTools → Console)
- [ ] All 7 sidebar items are present and clickable
- [ ] Clicking each sidebar item switches the active section (green highlight moves)
- [ ] "What it does" and "How it works" tabs switch correctly on every section
- [ ] Mermaid diagrams render in the "How it works" tab on all 7 sections (no raw `graph TB` text visible)
- [ ] File refs tags appear below each diagram
- [ ] Page is readable at 1280px wide without horizontal scroll

If any Mermaid diagram shows raw text instead of a rendered diagram, open DevTools Console — the error will identify which diagram has a syntax issue. Fix the `<pre class="mermaid">` block for that section and reload.

- [ ] **Step 4: Add `.superpowers/` to `.gitignore`**

Read `.gitignore` first, then append if not already present:

```bash
cd "/Users/macnas/Code/VS code/LogFire" && grep -q '.superpowers' .gitignore || echo '.superpowers/' >> .gitignore
```

- [ ] **Step 5: Commit**

```bash
cd "/Users/macnas/Code/VS code/LogFire" && git add docs/architecture/index.html .gitignore && git commit -m "$(cat <<'EOF'
feat: add static architecture documentation site with Mermaid diagrams

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

Expected output: `1 file changed` (index.html) or `2 files changed` (if .gitignore was updated).

---

## Self-Review

**Spec coverage:**

| Spec requirement | Covered |
|---|---|
| Single static HTML file, no server needed | ✅ Task 1 creates `docs/architecture/index.html` |
| Mermaid.js from CDN, no build step | ✅ `<script type="module">` import in `<head>` |
| Sidebar navigation with 7 sections | ✅ All 7 nav items in sidebar |
| "What it does" / "How it works" tabs per section | ✅ Both tabs on every section |
| Section 1: System Overview + graph diagram | ✅ `graph TB` with 6 nodes |
| Section 2: Request Flow + sequence diagram | ✅ `sequenceDiagram` with full lifecycle |
| Section 3: Agent Roles + delegation graph | ✅ `graph TD` + delegation note |
| Section 4: Tool Matrix + bipartite graph | ✅ `graph LR` agents → tools |
| Section 5: Integrations + context diagram | ✅ `graph TB` with all 6 systems |
| Section 6: Data Models + ER diagram | ✅ `erDiagram` with 5 entities |
| Section 7: Escalation Flow + flowchart | ✅ `flowchart TD` with colour-coded nodes |
| File opens via `file://` without errors | ✅ No `fetch()` calls, no CORS issues |
| `.superpowers/` in `.gitignore` | ✅ Step 4 |

**Placeholder scan:** No TBD, no TODO. All code blocks are complete.

**Type consistency:** No types to check — this is a static HTML file.
