# ADR 0019: Keep one versioned history with release tooling in release

- Status: Accepted
- Date: 2026-07-18
- Supersedes: ADR 0017 release-note ownership and snippet inclusion

## Context

ADR 0017 kept a root `CHANGELOG.md` as the canonical history and rendered it
inside a website wrapper through a Markdown snippet. The release helper kept an
empty `Unreleased` section at the top after every release.

That design created two visible release-note files, made the public site show
an empty pending heading above published versions, and split release knowledge
between a root guide and a general scripts directory. The helper also claimed
portable release-note filenames while the workflow staged only
`CHANGELOG.md`.

FastAPI demonstrates that release notes can be owned directly by the docs
tree. Pydantic demonstrates a cohesive root `release/` boundary and a versioned
history generated from merged pull requests during preparation.
Wireme already validates Conventional pull request titles, so merged pull
requests are a suitable input for generated draft notes.

## Decision

`website/docs/release-notes.md` is the only release-history source and contains
explicit version sections only. The documentation site renders that file
directly, and package metadata links to the rendered page. There is no rolling
`Unreleased` or `Latest Changes` section.

The preparation workflow asks GitHub to generate notes from merged pull
requests since the previous release tag. It prepends a dated version section
to the canonical history and opens a release pull request. A maintainer must
curate those generated notes before merging.

Release-specific implementation and maintainer guidance live together in
`release/`. General repository scripts remain in `scripts/`. All workflow and
test references use one explicit release-notes path instead of filename
detection.

Release distributions are built, smoke-tested, and attested before being
attached to the draft GitHub Release. Publishing makes the complete release
immutable; the protected PyPI job downloads, verifies, and publishes those
same assets.

## Consequences

- Positive: the repository, website, package metadata, draft release, and PyPI
  process share one release-history source.
- Positive: published documentation never presents an empty pending section as
  if it were a release.
- Positive: release automation is cohesive and transferable as one directory
  plus three workflows.
- Positive: immutable GitHub assets become the reviewed handoff to PyPI.
- Negative: upcoming changes are not visible in the release history before a
  release is prepared.
- Negative: a prepared version entry can reach the website while its complete
  draft release awaits maintainer publication.
- Negative: generated notes depend on clear pull request titles and still
  require maintainer curation.
- Follow-up: repositories adopting this setup must configure release-note
  labels, immutable releases, the aggregate required check, and Trusted
  Publishing.
