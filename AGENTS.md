# AGENTS.md

Canonical repository guidance for Claude Code and other coding agents.
CLAUDE.md is a symlink to this file; edit AGENTS.md only.

# Project purpose

wireme is a tiny, typed dependency injection facade built on FastDepends.

The framework-independent root API is intentionally small:

- Wired
- wired
- wire
- override_dependency

Wireme is DI-only. It never validates, coerces, or serializes arguments,
dependency results, or return values. FastDepends must always be invoked with
casting and result serialization disabled explicitly, including when Pydantic
is installed by an application or optional integration. Validation belongs at
application boundaries or inside the objects an application constructs.
Reject FastDepends CustomField markers; they are an upstream argument-processing
extension surface, not part of Wireme's dependency vocabulary.

The public root facade is src/wireme/__init__.py. Application code should
import public APIs from wireme, never from private modules.

FastAPI integration is optional and lives under wireme.fastapi. It must never
be re-exported from the wireme root.

The intended FastAPI public API is:

- FromWeb
- override_web_dependency

Do not add wrappers such as depends() or from_web() that merely rename
FastAPI's built-in Depends() without adding meaningful behavior.

# Commands

Use uv for everything. Never call pip directly, except "uv pip" targeting an
explicitly selected isolated environment.

- uv sync --all-extras --all-groups  ->  install everything
- uv run pytest tests/unit  ->  framework-independent tests
- uv run pytest tests/integration -m integration  ->  FastAPI integration tests
- uv run pytest tests/automation  ->  repository automation tests
- uv run pytest -m 'not integration'  ->  skip integration tests
- uv run pytest tests/unit/test_core.py::test_name  ->  single test
- uv run basedpyright  ->  type check (strict mode)
- uv run ruff check .  ->  lint
- uv run ruff format .  ->  format
- just check  ->  format check, lint, types, tests with coverage
- just examples  ->  run every documented example
- just build  ->  uv build --no-sources into a clean dist/
- just docs  ->  serve the docs site locally with live reload
- just docs-build  ->  build the docs site into website/site
- just smoke  ->  wheel and sdist smoke tests (core, missing extra, fastapi)
- just release-check  ->  check + examples + docs build + smoke
- just clean  ->  remove caches and build artifacts

Pytest is configured with --strict-config and --strict-markers. Coverage is
branch coverage with fail_under = 100. The integration marker is registered in
pyproject.toml; integration test modules declare:

    pytestmark = pytest.mark.integration

# Architecture

Architecture decisions are recorded in docs/adr (MADR-lite, append-only).
Public API changes require a new ADR; open questions live in
docs/adr/deferred-decisions.md.

User documentation: README.md is a thin landing page; depth lives in
website/docs (guide pages, recipes, the-wireme-way), served as a Zensical
site at https://wireme.mghalix.com and browsable on GitHub. Every public
capability must appear in at least one runnable example, indexed in
examples/README.md. When a capability is added, update the guide page, the
example, and the index together. Build the site with "just docs-build";
serve locally with "just docs".

Core package:

- src/wireme/__init__.py is the public facade.
- src/wireme/_impl.py contains the framework-independent implementation:
  wire, wired, Wired, override_dependency, PEP 695 alias resolution, and
  hiding injected parameters from public runtime signatures.
- src/wireme/_core.py isolates FastDepends imports and private compatibility
  boundaries. All FastDepends symbols enter the codebase through this module.
- src/wireme/py.typed marks the package as typed.

FastAPI integration:

- src/wireme/fastapi/__init__.py is its public facade.
- src/wireme/fastapi/_compat.py loads the optional FastAPI dependency and
  gives an actionable error when the extra is missing.
- src/wireme/fastapi/_dependencies.py implements FromWeb and dependency
  bridging. Bridged adapters are cached per (factory, use_cache) so overrides
  can find them.
- src/wireme/fastapi/_overrides.py implements nested-safe FastAPI overrides.
  Routes must be registered before entering an override context so all
  FromWeb bridges are known.

Core imports must work when FastAPI is not installed:

    import wireme

Importing the optional integration without its extra must raise
ModuleNotFoundError with this exact actionable message:

    wireme.fastapi is unavailable because the 'fastapi' extra is not installed. Install it with: uv add 'wireme[fastapi]'

tests/smoke/fastapi_missing.py asserts this message verbatim; keep them in
sync.

# FromWeb behavior

FromWeb has two meaningful modes.

Plain class or callable:

    service: FromWeb[UserService]

FastAPI owns the web-facing dependency. A class may use @wire (on the class,
which wires the constructor it defines, or on __init__ directly) so Wireme
resolves its internal dependencies.

Reusable Wireme alias:

    type UserServiceDep = Annotated[
        UserService,
        wired(get_user_service),
    ]

    service: FromWeb[UserServiceDep]

FromWeb must unwrap PEP 695 TypeAliasType and Annotated metadata, then bridge
the wired factory into a FastAPI-compatible dependency while preserving
Wireme's internal dependency graph, static type, cache configuration,
overrides, and resource lifecycle.

# Dependency completeness

Wireme must support the complete dependency forms provided by its FastDepends
foundation:

- synchronous factories
- asynchronous factories
- generator factories
- asynchronous generator factories
- nested dependencies
- callable objects
- functools.partial
- cached and uncached dependencies
- dependency overrides
- deterministic cleanup

Completeness applies to dependency graph and lifecycle behavior, not upstream
serializers, casting, validation, CustomField processing, or extension APIs.

Do not silently provide reduced behavior through the FastAPI integration.
Generator and async-generator dependencies must be supported with correct
FastAPI request lifecycle semantics, not rejected merely because bridging them
is more difficult.

# Optional dependencies

FastAPI remains an optional extra:

    uv add 'wireme[fastapi]'

Do not make FastAPI a core dependency.

TestClient-only dependencies such as httpx2 are development or smoke-test
dependencies, not public runtime requirements for wireme[fastapi].

# Testing layout

Keep test responsibilities separated:

    tests/
    |-- automation/
    |-- unit/
    |-- integration/
    |   `-- fastapi/
    |-- typing/
    `-- smoke/

- tests/automation contains tests for repository tooling such as release
  preparation. It is not part of the core library test suite.
- tests/unit contains framework-independent core behavior and public API tests.
- tests/integration/fastapi contains real FastAPI integration tests.
- tests/typing contains BasedPyright fixtures and is not collected by Pytest.
  It is type checked because basedpyright's include list covers it.
- tests/smoke runs built wheel and sdist artifacts in genuinely isolated
  environments. Smoke files are plain scripts, not pytest modules.

Do not name executable files fastapi.py, pytest.py, typing.py, inspect.py, or
after any installed package they import.

Tests should be concise, one behavior each, and use Given-When-Then structure.
Prefer real fixtures and small real integrations over mocking internals.

Coverage is expected to remain at 100 percent. A branch that can only be
tested in an isolated missing-extra environment may use a narrowly scoped
"pragma: no cover" only when a real artifact smoke test covers it.

# Artifact testing

Do not trust tests against an editable source checkout as packaging
validation.

Build with:

    uv build --no-sources

Validate metadata with:

    uvx twine check dist/*

Smoke tests must:

- install the built wheel or sdist into a fresh temporary virtual environment
- run from a temporary working directory
- avoid inheriting the repository's active virtual environment
- verify core installation without extras
- verify core installation does not include Pydantic
- verify the exact missing-FastAPI-extra error
- verify installation with wireme[fastapi]
- exercise a real FastAPI request
- verify Wireme preserves values even when FastAPI installs Pydantic
- verify generator cleanup behavior

Using "uv run --with" is not sufficient when it can reuse or layer over the
active project environment. Prefer creating a temporary environment with
"uv venv" and installing the exact artifact with "uv pip install --python".
Pass --refresh to uv pip install so a rebuilt artifact with an unchanged
version is never served stale from the uv cache. The scripts/smoke script
shows the pattern; just smoke runs it for the wheel and the sdist.

# Versioning

Wireme follows SemVer (docs/adr/0012). Below 1.0.0 the strict 0.x mapping
applies:

- Breaking API change -> minor bump (0.2.1 -> 0.3.0)
- New backward-compatible feature -> patch bump (0.2.1 -> 0.2.2)
- Bug fix -> patch bump (0.2.1 -> 0.2.2)

In 0.x the minor number is the breaking-change signal. Choose the next
version from the changelog content, not from feature size.

# Release process

Use uv for all dependency, build, and publishing operations. The build
backend is uv_build.

Before release:

    uv sync --all-extras --all-groups
    uv run coverage erase
    just release-check
    uvx twine check dist/*

CI (.github/workflows/ci.yml) must test Python 3.12, 3.13, and 3.14.

CI should have separate jobs for:

- core without optional FastAPI extras
- FastAPI integration with all extras
- built artifact smoke tests

The task runner intentionally has no release recipe. Local release commands
must remain side-effect-free. RELEASING.md is the canonical maintainer guide.
The release path is:

- workflow_dispatch on prepare-release.yml chooses a SemVer bump
- scripts/release.py updates pyproject.toml, uv.lock, and CHANGELOG.md
- a short-lived GitHub App token opens a release pull request and triggers CI
- merging that pull request makes create-draft-release.yml create the tag and
  a draft GitHub Release at the exact merge commit
- publishing the reviewed draft triggers release.yml

The publishing workflow verifies that the release came through the prepared
draft, the tag matches the pyproject.toml version, the changelog contains the
release, and the tagged commit belongs to default-branch history. It then:

- builds and tests without publishing credentials
- passes the verified artifacts to a separate publishing job bound to the
  pypi environment
- records GitHub build provenance
- publishes to PyPI with Trusted Publishing
- attaches the exact published artifacts to the existing GitHub Release

Repository settings must protect the pypi environment with required reviewers,
prevent self-review, and restrict deployments to v* tags. The workflow file
selects the environment but cannot configure those protections itself.

The release-automation environment owns RELEASE_APP_CLIENT_ID and
RELEASE_APP_PRIVATE_KEY for a GitHub App limited to contents and pull-request
write access. Do not replace it with the default GITHUB_TOKEN; pull requests
created by that token do not trigger normal CI. Do not use a maintainer's
personal token when a short-lived installation token is available.

Do not bump a version, create a tag, publish to PyPI, or create a GitHub release
locally. Release mutations belong to the reviewed workflows only.

Published artifacts are immutable. A broken release must be fixed by
publishing a new version.

# Writing style

Use ASCII only.

- No Unicode punctuation or decorative symbols.
- Use plain quotes and apostrophes.
- Use -> for arrows.
- Use ... for ellipses.
- Never use em-dash sentence breaks.
- Prefer clear, concise, professional prose.

# Python style

- Use uv, never pip directly, except through "uv pip" for an explicitly
  selected isolated environment.
- Use strong typing and BasedPyright strict mode.
- Prefer PEP 695 type statements for module-level aliases.
- Use assignment-style Annotated aliases where runtime frameworks must
  inspect a normal typing object rather than TypeAliasType.
- Use collections.abc abstractions.
- Always parameterize generic types.
- Annotate constants with Final[value_type].
- Public functions require useful docstrings.
- Use Google-style Args:, Returns:, Raises:, and Yields: sections where
  applicable.
- Document the condition causing each exception.
- Keep compatibility hacks isolated behind private modules.
- If using private FastDepends or FastAPI internals, add regression tests and
  constrain compatible dependency versions.
- Ruff: line length 88, target py312. Wired and wired are registered in
  flake8-bugbear extend-immutable-calls so B008 allows them in defaults.
- In docs and examples, declare injected parameters keyword-only, grouped
  after * at the end of the signature (docs/adr/0009).
- Docs and examples show the author-preferred form first; alternatives come
  after, framed as such (docs/adr/0011).
