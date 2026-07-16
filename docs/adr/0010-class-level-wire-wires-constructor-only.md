# ADR 0010: Class-level @wire wires the constructor only

- Status: Accepted
- Date: 2026-07-16

## Context

Decorating `__init__` works but reads as ceremony; users of other DI
libraries expect to decorate the class. The tempting extension - scanning
the class and auto-wiring every method that has wired-looking parameters -
is implicit magic: a reader cannot tell which methods are wrapped, it adds
import-time signature scanning plus per-call validation to methods that
never asked for it, and it multiplies edge cases (classmethods,
staticmethods, properties, inheritance).

## Decision

`@wire` on a class wires exactly the `__init__` the class defines itself and
returns the class; it is pure sugar for `@wire` on `__init__`. A class
without its own `__init__` is rejected with an actionable `TypeError`
instead of silently wrapping an inherited constructor. Methods keep their
own explicit `@wire`. Rejected: automatic method scanning.

## Consequences

- Positive: the preferred constructor-injection form is one decorator at
  the class head; injection remains visible where it happens.
- Negative: a second (equivalent) spelling for constructor injection
  exists; docs show the class form first (ADR 0011).
- Follow-up: dataclass field injection (`@wire` above `@dataclass`) is
  tracked in deferred-decisions.md.
