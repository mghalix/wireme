# Architecture Decision Records

One file per decision, numbered, append-only: a decision is never edited
into something else - it is superseded by a new ADR that links back. Format
is MADR-lite: Status / Context / Decision / Consequences. Statuses are
Proposed, Accepted, Rejected, or Superseded by NNNN.

Why keep these: (1) future contributors learn why, not just what; (2)
settled arguments do not get re-litigated; (3) the owner's design education
is preserved. Rejected options get their own record or a rejection note
inside the deciding ADR. Open questions that do not need an answer yet live
in deferred-decisions.md, not in ADRs.

Decisions 0001-0017 were recorded on 2026-07-16 while preparing the 0.1.1
release (core facade, FastAPI integration, style conventions, versioning
policy, the wire configuration surface, the documentation layout, project
defaults, member selection, and the documentation site). Decision 0018 was
recorded on 2026-07-17 to establish a strict DI-only boundary. Decision 0019
was recorded on 2026-07-18 to establish one versioned history, a cohesive
release tooling boundary, and immutable assets as the PyPI handoff.
