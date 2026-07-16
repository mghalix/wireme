# ADR 0008: FromWeb is the primary FastAPI pattern; wired endpoints are secondary

- Status: Accepted
- Date: 2026-07-16

## Context

`@wire` applied under a route decorator works today: dependencies resolve,
injected parameters stay out of the OpenAPI schema, query parameters keep
working, and the wrong decorator order fails loudly at registration
(verified empirically). It reads nicely and needs no `wireme.fastapi`
import. But it bypasses FastAPI's dependency system: generator dependencies
close when the endpoint returns (before the response is sent, breaking
streaming), and the dependencies are invisible to
`override_web_dependency` and `app.dependency_overrides`.

## Decision

`FromWeb` is the documented primary integration; it keeps FastAPI as the
owner of the request lifecycle. Wiring endpoints directly with `@wire` is a
supported, tested, documented secondary pattern with its tradeoffs stated.
No new endpoint-specific decorator is added.

## Consequences

- Positive: one blessed path for newcomers; the lighter pattern remains
  available and cannot silently rot (locked by integration tests).
- Negative: two ways to attach dependencies to an endpoint exist; docs
  mitigate by always showing `FromWeb` first (ADR 0011).
