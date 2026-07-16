# ADR 0012: SemVer with the strict 0.x mapping

- Status: Accepted
- Date: 2026-07-16

## Context

SemVer point 4 exempts major version zero: anything may change at any time,
and the public API is not considered stable until 1.0.0. The working
convention for 0.x shifts each rule down one slot. Without a recorded
policy, additive releases get labeled 0.(y+1).0 out of habit, wasting the
minor number's meaning as the breaking-change signal.

## Decision

Wireme follows SemVer. Below 1.0.0: breaking API change bumps minor
(0.2.1 -> 0.3.0); new backward-compatible features and bug fixes bump patch
(0.2.1 -> 0.2.2). From 1.0.0 the standard mapping applies. Published
artifacts are immutable; a broken release is fixed by publishing a new
version. Consequence applied immediately: the FastAPI integration release
is additive over 0.1.0, so it ships as 0.1.1, not 0.2.0.

## Consequences

- Positive: a 0.x minor bump is a reliable "read the changelog" signal for
  users; release numbering stops being a judgment call.
- Negative: feature-heavy patch releases look modest; the changelog carries
  the real weight.
