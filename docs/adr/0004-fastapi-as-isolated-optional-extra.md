# ADR 0004: FastAPI integration is an isolated optional extra

- Status: Accepted
- Date: 2026-07-16

## Context

Most Wireme users do not use FastAPI, and the core promise is a
framework-independent DI primitive. Making FastAPI a hard dependency would
bloat installs; mixing FastAPI names into the root namespace would blur the
ownership boundary.

## Decision

The integration lives in `wireme.fastapi`, installed via
`uv add 'wireme[fastapi]'`, and exposes exactly two names: `FromWeb` and
`override_web_dependency`. Nothing FastAPI-related is re-exported from the
wireme root. `import wireme` must always work without FastAPI. Importing
`wireme.fastapi` without the extra raises `ModuleNotFoundError` with one
exact actionable message (asserted verbatim by the missing-extra smoke
test). Rejected: wrappers such as `depends()` or `from_web()` that merely
rename FastAPI's `Depends()` without adding behavior.

## Consequences

- Positive: zero web-framework weight in core; a clean home for future
  integrations (`wireme.<framework>`).
- Negative: two import locations for FastAPI users.
- Follow-up: keep `tests/smoke/fastapi_missing.py` and
  `wireme/fastapi/_compat.py` message text in sync.
