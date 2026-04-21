# Connector Failure Runbook

## Symptoms
- Errors in `connector-service` spans
- Attributes show repeated retry attempts
- `is_exception = true` on spans named `connector.execute`

## Investigation Steps
1. Identify which connector type failed (span attribute: `connector.type`)
2. Check for external HTTP errors vs internal errors
3. If external (4xx/5xx from upstream): classify as external issue
4. If internal (exception in connector code): flag for Development
5. Check error recurrence pattern — intermittent vs persistent
