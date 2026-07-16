# ADR 0001: Build Wireme as a typed facade over FastDepends

- Status: Accepted
- Date: 2026-07-16

## Context

Writing a dependency resolution engine (nested graphs, sync and async
solving, generator lifecycles, caching, overrides) is a large maintenance
commitment. FastDepends already provides a correct engine, but its raw API
is verbose, weakly typed at call sites, and leaks injected parameters into
runtime signatures.

## Decision

Wireme is a small, opinionated, strongly typed facade over FastDepends. The
root API is intentionally tiny: `wire`, `wired`, `Wired`,
`override_dependency`, `WiremeError`, `ValidationError`. All FastDepends
symbols enter the codebase through the private boundary `wireme/_core.py`.
Wireme adds value through ergonomics: hidden injected parameters, PEP 695
alias support, nested-safe overrides, and typed factory overloads. It must
never expose less capability than FastDepends provides (see AGENTS.md
"Dependency completeness").

## Consequences

- Positive: tiny surface to learn and maintain; engine correctness is
  upstream's problem; strong typing end to end.
- Negative: coupled to FastDepends internals' behavior; the pinned range in
  pyproject.toml and the integration test suite are the compatibility
  contract.
- Follow-up: any use of an undocumented upstream contract must be isolated
  in `_core.py`, regression tested, and version constrained.
