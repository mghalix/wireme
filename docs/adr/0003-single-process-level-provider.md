# ADR 0003: One process-level dependency provider

- Status: Accepted
- Date: 2026-07-16

## Context

FastDepends supports multiple `Provider` instances and per-inject providers.
Exposing them would let users partition dependency graphs, at the cost of a
second concept to learn, provider-passing plumbing in every API, and
override semantics that depend on which provider a call was wired against.

## Decision

Wireme uses one private module-level provider for the whole process.
`override_dependency` mutates it and is documented for isolated tests and
application setup, not concurrent request-level mutation. Custom and scoped
providers are rejected for now.

## Consequences

- Positive: zero provider ceremony; overrides always find the dependency.
- Negative: no per-tenant or per-test-session graph isolation; parallel
  test processes (not threads) are the isolation boundary.
- Follow-up: request-scoped or instance-scoped providers are tracked in
  deferred-decisions.md; a future ADR must supersede this one to add them.
