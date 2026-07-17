# Release notes

Wireme follows [SemVer](https://semver.org) with the strict 0.x mapping:
breaking changes bump minor, features and fixes bump patch. Published
artifacts are immutable; a broken release is fixed by publishing a new
version.

## 0.2.0 - 2026-07-17

- Remove `cast` and `cast_result` from `wire` and `wired`; Wireme now preserves
  arguments, dependency results, and return values exactly as supplied.
- Remove `ValidationError` and `WiremeError` from the public root facade.
- Remove the Pydantic runtime dependency and explicitly disable every
  FastDepends serializer path, including FastAPI bridges.
- Constrain FastDepends to the tested 3.0.x line and add core and integration
  regressions for serializer-free behavior.
- Reject FastDepends CustomField markers so upstream argument-processing
  extensions cannot leak through Wireme's DI-only boundary.
- Make examples and strict documentation builds part of the release check,
  and enforce the DI-only core contract across the CI Python matrix.
- Remove the side-effecting local release recipe. Release preparation now uses
  a generated, reviewable pull request and draft GitHub Release, while the
  separated publisher retains tag, history, artifact, Trusted Publishing, and
  provenance checks.

## 0.1.1 - 2026-07-16

- Replace the repository and documentation identity with approved path-only
  SVG masters, deterministic typography, responsive dark and light banners,
  and a compact favicon derived from the same visual language.
- Centralize brand installation in the shared `repo-brand` command and remove
  the duplicated project-local installer and maintainer-only task recipe.
- Reuse one provider-neutral `social-preview.png` for GitHub, Open Graph, and
  Twitter metadata, with absolute website image URLs and an enforced safe area.
- Add the optional FastAPI integration `wireme.fastapi` with `FromWeb` and
  `override_web_dependency`, installed with `uv add 'wireme[fastapi]'`.
- `FromWeb[WiredClass]` lets FastAPI construct classes whose wired
  constructors resolve internal dependencies through Wireme.
- `FromWeb[WiredAlias]` bridges reusable PEP 695 dependency aliases into
  FastAPI while preserving the static type, nested resolution, cache
  configuration, overrides, and resource lifecycle.
- Bridged factories support sync, async, generator, and async-generator
  functions, callable objects, and `functools.partial`, with request-scoped
  cleanup that runs exactly once after the response, closes nested resources
  in reverse order, and receives endpoint exceptions.
- `override_web_dependency()` temporarily replaces direct FastAPI
  dependencies and bridged Wireme factories, is nested-safe and
  exception-safe, and accepts replacements with different parameter lists.
- Importing `wireme.fastapi` without the extra raises `ModuleNotFoundError`
  with an actionable install hint; `import wireme` never requires FastAPI.
- Document that explicit values for injected parameters must be passed by
  keyword.
- `@wire` now works on classes, wiring the constructor the class defines;
  a class without its own `__init__` is rejected with an actionable error.
- `@wire` accepts configuration: `cast` and `cast_result` control pydantic
  validation per function, and `requires` declares side-effect dependencies
  resolved on every call without appearing as parameters.
- Document singleton factories (eager module instance for fail-fast
  configuration, `functools.cache` for lazy creation) and clarify that
  `use_cache=True` caches once per wired call, not process-wide.
- Document and test applying `@wire` directly to FastAPI endpoints, including
  its lifecycle and override tradeoffs compared to `FromWeb`.
- Adopt the keyword-only convention for injected parameters (declared after
  `*`) across all documentation and examples.
- Record architecture decisions in `docs/adr` and document the SemVer 0.x
  versioning policy.
- Restructure documentation: README.md is a thin landing page and the full
  guide lives in `website/docs/guide` with one concept per page.
- Cover every capability with a runnable example and add the capability
  index `examples/README.md` (new: `nested.py`, `singletons.py`,
  `requires.py`, `validation.py`, `fastapi_endpoints.py`,
  `project_defaults.py`, `method_wiring.py`).
- Fix nested factories losing wired markers: factory signatures are now
  resolved when declared with `wired()` or `requires`, so PEP 695 aliases
  behind postponed annotations work at any nesting depth.
- Document project-wide defaults through bound decorators and the apply
  combinator pattern for wiring many methods at once.
- Cover pydantic parameter constraints without models (`Field`, pydantic
  types, custom validators, constrained factory parameters) with tests and
  `examples/field_constraints.py`.
- Cover all factory forms (classes, callable instances, static and bound
  methods, caller-argument sharing) with tests and `examples/factories.py`.
- Fix annotation resolution for locally defined names when `wire` is used
  through its configured form.
- Publish the documentation as a Zensical site at wireme.mghalix.com with
  a landing page, production recipes, and "The Wireme way" house-style page.

## 0.1.0 - 2026-07-15

- Add `wire`, `wired`, `Wired`, and `override_dependency`.
- Support sync, async, generator, and async-generator dependencies.
- Hide injected parameters from runtime signatures.
- Restore nested dependency overrides correctly.
