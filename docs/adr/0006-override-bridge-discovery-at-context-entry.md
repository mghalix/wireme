# ADR 0006: override_web_dependency discovers bridges at context entry

- Status: Accepted
- Date: 2026-07-16

## Context

`override_web_dependency` must override both direct FastAPI dependencies and
the adapters `FromWeb` generates for wired factories. The adapter registry
is global and populated when a `FromWeb[...]` annotation is first evaluated.
An override context cannot know about adapters that do not exist yet.

## Decision

The override context snapshots the known bridges for the original factory at
entry and installs `app.dependency_overrides` pairs for each. The
limitation is accepted and documented: a `FromWeb` annotation evaluated for
the first time inside the context is only overridden after the context is
entered again. A test asserts this behavior explicitly.

## Consequences

- Positive: simple, deterministic restore semantics (nested-safe and
  exception-safe by snapshot).
- Negative: route-registration order matters in the rare late-registration
  case; the docstring, README, and a dedicated test keep it discoverable.
