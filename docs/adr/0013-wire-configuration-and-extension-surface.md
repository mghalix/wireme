# ADR 0013: wire configuration (cast, cast_result, requires); rejected extension surfaces

- Status: Accepted
- Date: 2026-07-16

## Context

Wireme must not offer less than its FastDepends foundation (ADR 0001). An
audit on 2026-07-16 found three upstream capabilities without a Wireme
spelling: per-function casting control (`inject(cast=...)`), extra
side-effect dependencies (`inject(extra_dependencies=...)`), and the
library extension surfaces (`Provider` instances, `CustomField` markers,
the msgspec serializer).

## Decision

`wire` gains an optional configuration form alongside the bare decorator:
`@wire(cast=..., cast_result=..., requires=(...))`. `requires` accepts
plain factory callables (any supported form) resolved on every call without
appearing as parameters; they share the per-call cache and generator
factories clean up when the call finishes. Rejected from the public
surface: custom `Provider` instances (ADR 0003), the `CustomField` marker
API (the documented factory-based integration pattern covers the need
without exposing upstream's extension machinery), and the msgspec
serializer (Wireme depends on `fast-depends[pydantic]`; one validation
stack keeps behavior predictable).

## Consequences

- Positive: guard-style dependencies and hot-path validation control get
  first-class, typed spellings; capability parity with upstream holds.
- Negative: `wire` has two call shapes (bare and configured); overloads
  keep both fully typed.
- Follow-up: per-dependency configuration of `requires` entries (cache or
  cast flags) is tracked in deferred-decisions.md.
