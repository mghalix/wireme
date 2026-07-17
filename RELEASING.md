# Releasing

Wireme releases are prepared, reviewed, tagged, built, and published by GitHub
Actions. No local command changes the version, creates a tag, or pushes a
release.

## Release flow

```text
Run Prepare release and choose patch, minor, or major
    -> CI updates pyproject.toml, uv.lock, and CHANGELOG.md
    -> CI opens a release pull request
    -> review the version, changelog, and normal CI checks
    -> merge the release pull request
    -> CI creates a draft GitHub Release at that merge commit
    -> review and publish the draft
    -> CI rebuilds and verifies the distributions without publish credentials
    -> approve the protected pypi environment
    -> CI attests and publishes the verified artifacts
```

There is one active release lane. Preparation stops when another release pull
request or draft release already exists.

## One-time repository setup

### Release automation GitHub App

The preparation workflow needs a token that can create a branch and pull
request while still triggering normal pull-request CI. GitHub deliberately
suppresses most workflow events created with the default `GITHUB_TOKEN`, so the
workflow uses a short-lived GitHub App installation token instead of a personal
access token.

Create or reuse a GitHub App with these repository permissions:

- Contents: Read and write
- Pull requests: Read and write

Install it on this repository. Create a GitHub environment named
`release-automation`, then add:

- Environment variable `RELEASE_APP_CLIENT_ID`
- Environment secret `RELEASE_APP_PRIVATE_KEY`

The same App can be installed on another owned repository, which makes this
setup reusable without tying automation to a maintainer's personal token.

### PyPI publishing

Create a GitHub environment named `pypi` and configure:

- required reviewers
- prevent self-review when the maintainer team permits it
- a deployment tag rule restricted to `v*`

Configure a PyPI Trusted Publisher for:

- repository: `mghalix/wireme`
- workflow: `release.yml`
- environment: `pypi`

No PyPI API token belongs in GitHub secrets.

### Default branch

Protect the default branch and require the normal CI checks on release pull
requests. If an automatically opened release pull request has no CI run, do not
merge it; the GitHub App credentials or installation are incomplete.

## Prepare a release

1. Make sure `CHANGELOG.md` contains the intended entries under
   `## Unreleased`.
2. Open GitHub Actions -> Prepare release -> Run workflow.
3. Choose the bump:
   - Below 1.0.0, breaking change -> minor.
   - Below 1.0.0, feature or fix -> patch.
   - From 1.0.0, use standard SemVer.
4. Optionally enter a release date; otherwise CI uses the current date.
5. Review the generated release pull request and merge only after CI passes.
6. Review the resulting draft GitHub Release and select Publish release.
7. Approve the `pypi` deployment when GitHub requests it.

The preparation helper is `scripts/release.py`. It supports:

```text
uv run python scripts/release.py current-version
uv run python scripts/release.py release-tag
uv run python scripts/release.py release-notes
uv run python scripts/release.py verify-tag v0.1.2
```

Its `prepare` command is reserved for the preparation workflow because it
changes version metadata. Local release checks remain side-effect-free:

```text
just release-check
```

## What the workflows verify

Before publishing, the workflows require all of the following:

- the release pull request came from this repository's `release/` branch
- the release target is the merged pull-request commit on the default branch
- no release tag existed before the draft was created
- the GitHub Release was created by the draft-release workflow
- the published release still points to the recorded draft target
- the tag equals `v` plus `[project].version`
- the changelog has a non-empty section for that version
- the tagged commit remains in default-branch history
- tests, types, lint, examples, strict docs, metadata checks, and isolated
  wheel and source-distribution smoke tests pass

The build job has no publishing credentials. Only its uploaded, verified
artifacts reach the protected publishing job. Publishing uses Trusted
Publishing, records GitHub provenance, skips identical files already present
on PyPI during a safe rerun, and attaches the exact artifacts to the GitHub
Release.

## Recovery

- Bad release pull request -> close it without merging, correct `Unreleased`,
  and run Prepare release again.
- Bad draft -> do not publish it. Delete the draft and any associated tag in
  GitHub, correct the release metadata through a pull request, and prepare it
  again.
- Failed verification before PyPI -> fix the problem through a normal pull
  request, then prepare a new release.
- Published release -> never replace its artifacts. Fix the problem in a new
  version.

## Reuse in another uv project

Copy these files:

- `scripts/release.py`
- `.github/workflows/prepare-release.yml`
- `.github/workflows/create-draft-release.yml`
- `.github/workflows/release.yml`

The reusable assumptions are intentionally small:

- static SemVer in `[project].version`
- a uv lockfile
- `CHANGELOG.md` or `release-notes.md` with `## Unreleased`
- headings formatted as either `## X.Y.Z - YYYY-MM-DD` or
  `## [X.Y.Z] - YYYY-MM-DD`; the existing style is preserved
- release tags prefixed with `v`

Then update the project-specific PyPI URL, build/test commands, smoke tests,
repository name in the Trusted Publisher, and environment configuration. Keep
action references and the uv version pinned to reviewed immutable versions.

Storix already uses static SemVer, uv, `release-notes.md`, bracketed headings,
and `v` tags. Before transferring this flow, add `## Unreleased` to its release
notes and move pending changes there. The helper will detect the filename and
preserve its bracketed heading style automatically.
