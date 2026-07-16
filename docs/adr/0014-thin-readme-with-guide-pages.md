# ADR 0014: Thin README with one-concept guide pages

- Status: Accepted
- Date: 2026-07-16

## Context

The README grew into a full manual (~650 lines). A PyPI/GitHub landing page
should sell the library and hand off in under a minute; a long scroll buries
the preferred-way-first teaching (ADR 0011). The owner already runs a
zensical + Cloudflare Pages docs pipeline for another project, so a real
docs site costs almost nothing once content is page-structured.

## Decision

README.md is a landing page: pitch, install, a sixty-second tour, a
documentation table, and the public API tables. Depth lives in
docs/guide/*.md, one concept per page in reading order, each ending with a
link to its runnable example. Every public capability must appear in at
least one runnable example, indexed in examples/README.md (the examples
directory is capability coverage, like tests are code coverage). README
links use absolute GitHub URLs so PyPI rendering works; guide pages link
relatively.

## Consequences

- Positive: fast onboarding; pages map one-to-one onto a future zensical
  nav, so publishing a site is a scaffold task, not a rewrite.
- Negative: two places to update when behavior changes (guide page and
  example); the examples index is the checklist.
- Follow-up: publishing docs/guide as a zensical site on the owner's domain
  is tracked in deferred-decisions.md.
