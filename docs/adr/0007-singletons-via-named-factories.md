# ADR 0007: Singletons are named factories, not lambdas

- Status: Accepted
- Date: 2026-07-16

## Context

`use_cache=True` caches once per wired call, not process-wide, so it cannot
create singletons. Users reach for `wired(lambda: instance)`, but every
`wired(lambda: ...)` call site creates a distinct factory object, so
`override_dependency` cannot target the dependency (verified empirically)
and error messages lose the factory name.

## Decision

The documented singleton patterns are named module-level factories. For
fail-fast configuration (for example pydantic settings validating the
environment), create the instance eagerly at module scope and return it
from a named factory. For lazy creation, decorate a zero-argument factory
with `functools.cache`. `wired(lambda: ...)` is rejected in documentation
and examples.

## Consequences

- Positive: stable factory identity keeps overrides and FromWeb bridging
  working; eager pattern fails at import, before requests.
- Negative: one extra function definition per singleton; no enforcement
  against lambdas (documentation only).
