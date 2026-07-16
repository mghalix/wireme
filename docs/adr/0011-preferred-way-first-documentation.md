# ADR 0011: Documentation shows the preferred way first

- Status: Accepted
- Date: 2026-07-16

## Context

Wireme's audience includes developers who do not know DI and do not want to
evaluate options. Readers copy the first code block they see and often skip
the prose around it. A doc that shows a workable-but-second-best form first
and corrects it in a note transfers the wrong habit.

## Decision

In every README section, example, and docstring, the first code shown is
the author-preferred way: the cleanest, safest, most efficient form,
already following house conventions (keyword-only injected parameters,
class-level wire for constructors, named factories, FromWeb first for
FastAPI). Alternatives and escape hatches appear only after the preferred
form, framed as such. Examples stay concise, focused, and atomic: one idea
per example.

## Consequences

- Positive: copy-paste transfers the house style; options narrow by
  default without hiding that they exist.
- Negative: doc edits must consider ordering, not just correctness; this
  ADR is the checklist item for reviews.
