# ADR 0016: Member selection stays out of wire; compose with an apply combinator

- Status: Accepted
- Date: 2026-07-16

## Context

After ADR 0010 (class-level `@wire` wires only the constructor), the next
request is optional method scanning: `@wire(include=..., exclude=...)` on a
class. Selection semantics are a domain of their own (allowlists, deny
lists, private-name gating, inherited members) and they are not specific to
dependency injection; the same selection is wanted for tracing, timing, and
console scopes in other tooling.

## Decision

`wire` gains no `include` or `exclude` parameters. The sanctioned route is
composition with a generic apply combinator that applies any per-function
decorator to explicitly named methods of a class:

    @apply(wire, include=("load", "reload"))
    class Loader: ...

Wireme documents the pattern with a runnable example
(examples/method_wiring.py) but does not ship `apply`: decorator
application machinery is not dependency injection, and one project-owned
`apply` should serve every decorator rather than each tool growing its own
selection flags.

## Consequences

- Positive: wire's contract stays one sentence; selection rules live in
  one place per project and work for every decorator.
- Negative: users must copy or import an `apply` helper; the example is
  the reference implementation.
