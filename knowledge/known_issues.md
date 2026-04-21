# Known Issues Reference

## MS Throttling — Connector 429/503

When the Microsoft connector receives 429 (Too Many Requests) or 503 (Service Unavailable)
responses, the sync-worker service will log errors with message containing "ThrottlingException"
or "ServiceUnavailableException". Check for these in the span attributes.

This is an external issue, not a platform bug. Check if multiple tenants are affected.

## Race Condition — Duplicate State Write

Concurrent span execution in the state-manager service can cause duplicate key errors on the
`tenant_state` table. Look for overlapping span timestamps on spans named `state.write`.

## Auth Token Expiry

If spans show 401 responses from the identity service, the customer's connector auth token
may have expired. Check spans tagged `auth.refresh` for failure count.
