# ADR 0002: Hide injected parameters; explicit values win, keyword-only

- Status: Accepted
- Date: 2026-07-16

## Context

Injected parameters are implementation detail to callers. Leaving them in
`inspect.signature()` confuses help(), editors, and web frameworks that
introspect signatures. Separately, callers sometimes want to hand a
dependency in explicitly for one-off composition. FastDepends' argument
mapping skips dependency-parameter names when filling positional arguments,
so a positional value aimed at an injected parameter is silently dropped and
the dependency is resolved anyway (verified empirically, 2026-07-16).

## Decision

`@wire` removes injected parameters from the public runtime signature. An
explicit keyword argument takes precedence over injection; this is a
feature, not a bug, and `@wire` does not reject it. Only the keyword form is
supported: the positional form is undefined behavior inherited from
upstream and is documented as such. Docs and examples declare injected
parameters keyword-only (after `*`, ADR 0009) so type checkers reject the
positional call statically.

## Consequences

- Positive: clean public signatures; one-off composition stays possible;
  tests use `override_dependency` for graph-wide replacement.
- Negative: the silent positional drop still exists at runtime for code
  that ignores the convention; rejected: runtime validation of extra
  positional arguments, because it would add per-call binding cost to every
  wired call (revisit in deferred-decisions.md if it bites users).
