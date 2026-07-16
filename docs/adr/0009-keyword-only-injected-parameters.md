# ADR 0009: Injected parameters are declared keyword-only

- Status: Accepted
- Date: 2026-07-16

## Context

Injected parameters are never meant to be passed by consumers, and a
positional value aimed at one is silently dropped at runtime (ADR 0002).
There is no benefit to injected parameters being positional-capable.

## Decision

All first-party documentation and examples declare injected parameters
keyword-only, grouped after `*` at the end of the signature:

    @wire
    def create_user(username: str, *, database: DatabaseDep = Wired()) -> None: ...

The `*` makes the dependency block visually distinct, forces explicit
overrides to be keyword calls, and turns the silent positional drop into a
static type error. This is a convention, not a runtime rule: `@wire` still
accepts positional-capable dependency parameters for compatibility.

## Consequences

- Positive: the runtime footgun becomes a type-checker error; signatures
  read as "inputs, then wiring".
- Negative: slightly more ceremony in signatures; existing user code is
  unaffected.
- Follow-up: runtime enforcement (warn or error on positional-capable
  dependency parameters) is tracked in deferred-decisions.md.
