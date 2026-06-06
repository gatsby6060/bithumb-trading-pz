---
trigger: model_decision
description: Applies when generating or modifying code that calls Bithumb API endpoints, to handle Rate Limiting, HTTP 429 Too Many Requests, and retry policies.
---
# Bithumb Rate Limiting & Retry Rule

This rule ensures compliance with Bithumb's API request limits and robust handling of HTTP 429 (Too Many Requests) responses.

## Constraints & Requirements

1. **Check Local Guides**:
   - Refer to [api-요청-수-제한-안내.md](file:///c:/260606coin/.agents/skills/bithumb-api-helper/guides/api-요청-수-제한-안내.md) for the exact rate limits of the endpoint being integrated (Public vs. Private).

2. **Implement Rate Limiters**:
   - For high-frequency trading logic, enforce client-side rate limiters or token-bucket delays to avoid exceeding Bithumb's limits.

3. **Handle HTTP 429 Responses**:
   - All API client implementations must catch HTTP `429 Too Many Requests` status codes.
   - Implement **Exponential Backoff** with jitter for request retries when a `429` error is encountered.
   - Fail gracefully or pause trading activities if the error persists.
