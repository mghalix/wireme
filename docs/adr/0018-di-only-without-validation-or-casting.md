# ADR 0018: Keep Wireme DI-only without validation or casting

- Status: Accepted
- Date: 2026-07-17
- Supersedes: ADR 0001 capability parity and public error facade, ADR 0013
  casting surface, ADR 0015

## Context

Wireme presents itself as a tiny dependency injection facade. Its original
FastDepends configuration also installed Pydantic, validated arguments and
factory inputs, coerced dependency and return values, and exposed validation
errors. Those behaviors cross the dependency injection boundary: they can
change ordinary Python values, conceal incorrect factory results, add hot-path
work, and make application behavior depend on which serializer libraries are
installed.

FastDepends discovers an installed serializer automatically. Removing the
Pydantic package extra is therefore insufficient when an application already
uses Pydantic or FastAPI. Wireme must select serializer-free behavior
explicitly at every FastDepends entry point.

## Decision

Wireme performs dependency resolution and lifecycle management only. It never
validates, coerces, or serializes arguments, dependency results, or return
values.

The public `wire` API keeps only `requires`; the public `wired` API keeps only
`use_cache`. `cast` and `cast_result` are removed rather than retained as
permanently false options. `ValidationError` and `WiremeError` are removed from
the root facade because Wireme no longer produces either error. `WiremeError`
was an alias of FastDepends' `FastDependsError`, which Wireme never raised
directly; in the supported 3.0.x line that base is used by `ValidationError`.
Dependency construction and call failures continue to surface as their ordinary
Python or upstream exceptions, so removing the aliases does not alter dependency
resolution.

All calls into FastDepends explicitly select `cast=False`,
`cast_result=False`, `serializer_cls=None`, and `serialize_result=False` as
applicable. The core dependency is FastDepends without serializer extras and
is constrained to the tested 3.0.x line. Contract tests cover direct calls,
nested factories, dependency results, built artifacts without Pydantic, and
FastAPI bridges where Pydantic is installed.

FastDepends CustomField markers are rejected. They can parse or replace
incoming arguments independently of the serializer and are an upstream
framework-extension surface, not part of Wireme's dependency vocabulary.

Caching, dependency overrides, nested graph resolution, side-effect
dependencies, asynchronous factories, generator resources, and deterministic
cleanup remain: they are dependency graph or lifecycle concerns.

FastAPI remains responsible for validating HTTP-facing input in the optional
integration. Applications that need validation elsewhere perform it at their
own boundary or inside the models and constructors they choose.

## Consequences

- Positive: Wireme has four framework-independent public names and one clear
  responsibility.
- Positive: values retain ordinary Python semantics and cannot be silently
  transformed by the DI layer.
- Positive: core installation no longer brings Pydantic and dependency calls
  avoid serializer work.
- Negative: removing public names and options is a breaking change, requiring
  the next minor release under the strict 0.x versioning policy.
- Negative: users relying on Wireme validation must move it to an explicit
  application boundary.
