# ADR 0005: One universal async-generator bridge for FromWeb

- Status: Accepted
- Date: 2026-07-16

## Context

Bridging wired factories into FastAPI must preserve the full FastDepends
lifecycle: sync, async, generator, and async-generator factories, callable
objects, partials, nested resources, caching, and overrides. The 0.1-era
prototype wrapped factories with `inject()` wrappers, which close nested
resources when the factory returns (before the response) and cannot
represent generator factories at all, so it rejected them.

## Decision

Every bridged factory uses one adapter shape: an async generator function
that runs `CallModel.asolve(stack=..., cache_dependencies={}, nested=True)`
inside its own `AsyncExitStack` and yields the resolved value. FastAPI
detects it natively and enters it on the request-scoped exit stack, so
FastAPI owns the request lifecycle: values live until the response (and
streaming body) completes, endpoint exceptions propagate into factory
generators, and nested resources close in reverse order. Adapters are
cached per `(factory, config)` for stable override identity; unhashable
factories are rejected with an actionable `TypeError`.

## Consequences

- Positive: one code path for every factory form; no reduced behavior
  versus core Wireme; no FastAPI private APIs.
- Negative: relies on the undocumented keyword contract of
  `CallModel.asolve` (documented in `_core.py`, regression tested,
  version constrained per ADR 0001).
