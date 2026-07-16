# The Wireme way

Wireme is opinionated so you do not have to be. Every rule below is the
first form shown in the docs, and each links to the decision record that
argued it out. Follow them and the codebase reads one way everywhere.

## Declare dependencies with the `type` keyword

Prefer PEP 695 `type` aliases for dependencies. The alias carries the
static type and the wiring together, is checked at maximum strictness, and
gives the dependency one name across the whole project:

```python
type DatabaseDep = Annotated[Database, wired(get_database)]
type Limit = Annotated[int, Field(gt=0, le=100)]
```

An alias is also the unit FastAPI bridging understands: `FromWeb[DatabaseDep]`
unwraps it and preserves the exposed type exactly.

## Injected parameters go after `*`

Declare injected parameters keyword-only, grouped at the end of the
signature:

```python
@wire
def create_user(username: str, *, database: DatabaseDep = Wired()) -> None: ...
```

Dependencies are never passed by position, and a positional value aimed at
an injected slot is silently ignored at runtime, so the `*` turns that
footgun into a type-checker error. Signatures read as "inputs, then
wiring". ([ADR 0009](https://github.com/mghalix/wireme/blob/main/docs/adr/0009-keyword-only-injected-parameters.md))

## `@wire` marks entry points; factories stay undecorated

`@wire` goes on the functions your code calls. Factories, including guards
passed to `requires`, are recipes the engine calls: they stay plain
functions and are never invoked directly once they declare `Wired()`
parameters of their own.

## Wire classes at the class head

Constructor injection uses the class decorator, which wires exactly the
`__init__` the class defines and nothing else. Methods keep their own
explicit `@wire`; there is no method scanning, by design.
([ADR 0010](https://github.com/mghalix/wireme/blob/main/docs/adr/0010-class-level-wire-wires-constructor-only.md))

```python
@wire
class UserService:
    def __init__(self, *, database: DatabaseDep = Wired()) -> None: ...
```

## Singletons are named factories

A module-level instance behind a named factory fails fast at import; a
`functools.cache` factory creates lazily. Never `wired(lambda: service)`:
each lambda is a distinct factory, so overrides cannot target it.
([ADR 0007](https://github.com/mghalix/wireme/blob/main/docs/adr/0007-singletons-via-named-factories.md))

## `FromWeb` first for FastAPI

`FromWeb` keeps FastAPI as the owner of the request lifecycle: resources
live through streaming, endpoint exceptions reach your generators, and
`override_web_dependency` sees everything. Wiring endpoints directly with
`@wire` is supported, but it is the secondary form with documented
tradeoffs. ([ADR 0008](https://github.com/mghalix/wireme/blob/main/docs/adr/0008-fromweb-primary-wired-endpoints-secondary.md))

## Project defaults are a binding, not a global

```python
# myapp/di.py
wire = wireme.wire(cast=False, cast_result=False)
```

Import that binding everywhere instead of configuring a process-global,
which would be import-order dependent and would leak into libraries.
([ADR 0015](https://github.com/mghalix/wireme/blob/main/docs/adr/0015-project-defaults-via-bound-decorators.md))

## Explicit values are keyword-only and win

`create_user("mo", database=TestDatabase())` beats injection for one-off
composition. For test suites, prefer `override_dependency` so every nested
dependency sees the replacement.

All decisions, including rejected alternatives and open questions, live in
the [ADR index](https://github.com/mghalix/wireme/blob/main/docs/adr/README.md).
