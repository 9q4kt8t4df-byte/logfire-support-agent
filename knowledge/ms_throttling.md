# MS Throttling Investigation Runbook

## Symptoms
- HTTP 429 or 503 in spans from `connector-service`
- Error message contains: ThrottlingException, RetryAfter, ServiceUnavailableException
- Spike in error rate starting at a consistent time

## Investigation Steps
1. Query spans for the tenant where `http.status_code = 429` or `http.status_code = 503`
2. Check span attribute `connector.provider` — confirm it is "microsoft"
3. Note the `start_timestamp` of the first throttling span
4. Check smoke-detector: MS throttling often affects multiple tenants simultaneously
   (Microsoft applies throttling at tenant or subscription level)

## Escalation Priority
- Single tenant: P3 — advise customer to check their MS subscription limits
- Multiple tenants (>3): P1 — platform-wide MS subscription or IP-level throttling
