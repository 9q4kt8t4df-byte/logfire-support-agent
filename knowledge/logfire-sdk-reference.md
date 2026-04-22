# Logfire SDK Reference — Trace & Span Model

Source: https://pydantic.dev/docs/logfire/api/logfire/

This document explains how Logfire traces are structured so the investigator agent can correctly interpret query results from the MCP server.

---

## Trace Hierarchy

Logfire traces follow the OpenTelemetry model:
- A **trace** is a tree of **spans** sharing a `trace_id`
- A **span** represents a unit of work with a start time, end time, and attributes
- Spans have parent-child relationships via `parent_span_id`
- A **root span** has no parent

When reading a trace, look for:
- The root span — its name and attributes describe the top-level operation
- Child spans — each represents a sub-operation (DB query, external call, LLM request)
- Error spans — any span with `otel.status_code = ERROR` or an exception attribute

---

## Log Severity Levels

`logfire.trace()` → `logfire.debug()` → `logfire.info()` → `logfire.notice()` → `logfire.warning()` → `logfire.error()` → `logfire.fatal()`

Error-class spans to prioritise during investigation: `error`, `fatal`, `exception` (the last includes a full stack trace in `exception.stacktrace`).

---

## Span Attribute Patterns by Instrumentation

### FastAPI / Starlette (`logfire.instrument_fastapi`)
Root span name: `{method} {route}` e.g. `GET /api/chat`
Key attributes:
- `http.method`, `http.url`, `http.status_code`
- `http.request.header.*` (if `capture_headers=True`)
- `http.response.body` (if body capture enabled)

### Anthropic SDK (`logfire.instrument_anthropic`)
Span name: `Anthropic {method}` e.g. `Anthropic chat`
Key attributes:
- `gen_ai.system` = `"anthropic"`
- `gen_ai.request.model` — model name
- `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`
- `gen_ai.response.finish_reason` — why the model stopped
- Tool call spans appear as child spans with `gen_ai.tool.name`

### httpx (`logfire.instrument_httpx`)
Span name: `{method} {url}`
Key attributes:
- `http.method`, `http.url`, `http.status_code`
- `http.request.body` / `http.response.body` (if capture enabled)

### SQLAlchemy / asyncpg (`logfire.instrument_sqlalchemy`, `instrument_asyncpg`)
Span name: `{db.operation} {db.name}`
Key attributes:
- `db.system`, `db.name`, `db.statement` (the SQL query)
- `db.operation` — SELECT / INSERT / UPDATE
- `exception.message` if a DB error occurred

### Custom spans (`logfire.span`)
Any span created with `with logfire.span("name", **attrs):`
Attributes are whatever the application passes — check `logfire.info()` / `logfire.error()` calls in the codebase for field names.

---

## Error Investigation Patterns

**Identifying the root cause span:**
1. Find the deepest span with `otel.status_code = ERROR`
2. Read `exception.type`, `exception.message`, `exception.stacktrace`
3. Check its parent span for context (what operation triggered it)

**Throttling / rate limit errors:**
- HTTP 429 → look for `http.status_code = 429` on httpx or requests spans
- Often on child spans of an Anthropic or Workato API call

**Timeout errors:**
- `exception.type` contains `Timeout` or `TimeoutError`
- Look for spans where `duration_ms` is unusually high relative to siblings

**Configuration errors:**
- `exception.type` contains `ValidationError` or `ConfigurationError`
- Usually on startup spans, not request spans

---

## Metrics

`logfire.metric_counter()`, `metric_histogram()`, `metric_gauge()` emit OpenTelemetry metrics (not spans). These are available in Logfire dashboards but not returned by the trace query MCP tools. If investigating a performance issue, ask the engineer to check Logfire dashboards for metric trends in addition to trace analysis.

---

## Key Logfire Query Fields

When using the MCP tools, these attributes are most useful for filtering:

| Field | Use |
|---|---|
| `otel.status_code` | `ERROR` to find failing spans |
| `exception.message` | Filter by error text |
| `http.status_code` | Filter by HTTP error code |
| `service.name` | Filter by microservice |
| `deployment.environment` | Filter by env (prod/staging) |
| `tenant_id` | Filter by customer tenant (if instrumented) |
| `gen_ai.request.model` | Filter Anthropic/LLM spans |
| `duration_ms` | Find slow spans |

---

## Logfire MCP Tools Available to the Agent

The investigator uses these MCP-backed tools:
- `query_traces(service, time_range, filters)` — list recent traces matching criteria
- `get_trace_detail(trace_id)` — full span tree for a single trace
- `get_service_logs(service, time_range, level)` — log entries (not spans)
- `get_service_error_rate(service, time_range)` — aggregated error counts

When a trace shows unexpected structure, cross-reference with this document to understand what instrumentation library produced each span.
