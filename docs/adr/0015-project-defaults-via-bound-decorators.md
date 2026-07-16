# ADR 0015: Project-wide defaults via bound decorators, not global config

- Status: Accepted
- Date: 2026-07-16

## Context

Users want project-wide preferences, for example "never cast anything". A
process-global configuration object (`wireme.configure(cast=False)`) is the
obvious spelling but has structural flaws: decorators evaluate at import
time, so behavior depends on whether configuration ran before or after each
module was imported, and one process owns one setting, so an application's
preference silently changes the behavior of every library that uses Wireme
internally.

## Decision

The configured form of `wire` already returns a reusable decorator, and
that is the supported mechanism for project defaults: bind options once in
a project module (`myapp/di.py: wire = wireme.wire(cast=False)`) and import
the binding everywhere. It works on functions, methods, and classes, is
explicit, import-order safe, and scoped to the code that imports it.
Rejected: mutable process-global configuration.

## Consequences

- Positive: zero new API; defaults are visible in code and reviewable;
  libraries and applications cannot fight over one global.
- Negative: a bound decorator accepts no further per-site configuration;
  deviating call sites use the full `wireme.wire(...)` form.
