# wireme

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/mghalix/wireme/main/.github/assets/wireme-banner-light.png">
    <img src="https://raw.githubusercontent.com/mghalix/wireme/main/.github/assets/wireme-banner.png" alt="wireme - tiny, typed dependency injection for Python" style="width: 100%; max-width: 880px;">
  </picture>
</p>

Tiny, typed dependency injection for Python. Resolve the graph. Touch nothing
else.

Powered by FastDepends, Wireme keeps dependency injection explicit and small:

```python
from wireme import Wired, override_dependency, wire, wired
```

- `@wire` enables dependency resolution for a class constructor, function,
  or method.
- `wired(factory)` declares how a dependency is created.
- `Wired()` marks a reusable `Annotated` dependency as caller-optional.
- `override_dependency()` temporarily replaces a dependency in tests.

Wireme only resolves dependencies. It never validates or coerces arguments,
dependency results, or return values; application boundaries own those
concerns.

## Installation

```bash
uv add wireme
```

With the optional FastAPI integration:

```bash
uv add 'wireme[fastapi]'
```

Wireme requires Python 3.12 or newer.

## Sixty-second tour

Declare a dependency once, inject it anywhere. Injected parameters go after
`*` and disappear from the public signature:

```python
from typing import Annotated

from wireme import Wired, wire, wired


class Database:
    def write(self, value: str) -> None:
        print(f"writing: {value}")


def get_database() -> Database:
    return Database()


type DatabaseDep = Annotated[Database, wired(get_database)]


@wire
def create_user(username: str, *, database: DatabaseDep = Wired()) -> None:
    database.write(username)


create_user("mo")  # database is resolved automatically
```

Classes wire their constructors; tests swap factories:

```python
from wireme import override_dependency


@wire
class UserService:
    def __init__(self, *, database: DatabaseDep = Wired()) -> None:
        self._database = database

    def list_users(self) -> list[str]:
        return []


def get_test_database() -> Database:
    return Database()


with override_dependency(get_database, get_test_database):
    UserService()  # built against the test database
```

With FastAPI, the same wired class plugs into endpoints while FastAPI keeps
ownership of the request lifecycle:

```python
from fastapi import FastAPI

from wireme.fastapi import FromWeb


app = FastAPI()


@app.get("/users")
def list_users(*, service: FromWeb[UserService]) -> list[str]:
    return service.list_users()
```

## Documentation

Rendered documentation lives at [wireme.mghalix.com](https://wireme.mghalix.com),
including recipes and the house style guide. The same pages are browsable
in the repository; the guide covers one concept per page, in reading order:

| Page | What it covers |
| --- | --- |
| [Getting started](https://github.com/mghalix/wireme/blob/main/website/docs/guide/getting-started.md) | Install, wire a function, reusable dependencies |
| [Wiring classes](https://github.com/mghalix/wireme/blob/main/website/docs/guide/classes.md) | Constructor and method injection |
| [The dependency graph](https://github.com/mghalix/wireme/blob/main/website/docs/guide/dependency-graph.md) | Nesting, per-call caching, singletons |
| [Resources](https://github.com/mghalix/wireme/blob/main/website/docs/guide/resources.md) | Async factories and generator cleanup |
| [Testing](https://github.com/mghalix/wireme/blob/main/website/docs/guide/testing.md) | Overrides and explicit values |
| [Side-effect dependencies](https://github.com/mghalix/wireme/blob/main/website/docs/guide/side-effects.md) | Guards and auditing with `requires` |
| [Protocol dependencies](https://github.com/mghalix/wireme/blob/main/website/docs/guide/protocols.md) | Depending on interfaces |
| [FastAPI integration](https://github.com/mghalix/wireme/blob/main/website/docs/guide/fastapi.md) | `FromWeb`, request-scoped resources, web overrides |
| [Building integrations](https://github.com/mghalix/wireme/blob/main/website/docs/guide/extending.md) | Wireme as your project's DI primitive |

Every capability also has a small runnable example; see the
[example index](https://github.com/mghalix/wireme/blob/main/examples/README.md).

## Public API

| Name                  | Purpose                                                         |
| --------------------- | --------------------------------------------------------------- |
| `wire`                | Decorate a class, function, or method and enable dependency resolution. Accepts side-effect dependencies through `requires`. |
| `wired`               | Declare a dependency factory and its per-call cache behavior.   |
| `Wired`               | Mark an `Annotated` dependency as caller-optional.              |
| `override_dependency` | Temporarily replace a factory, with nested restoration.         |

The optional `wireme.fastapi` integration adds:

| Name                      | Purpose                                                        |
| ------------------------- | -------------------------------------------------------------- |
| `FromWeb`                 | Annotate endpoint parameters with classes or wired aliases.    |
| `override_web_dependency` | Temporarily replace a web dependency, with nested restoration. |

## Why Wireme instead of importing FastDepends directly?

FastDepends provides the resolution engine. Wireme provides a deliberately
small, opinionated facade with:

- A cohesive `wire`, `wired`, and `Wired` vocabulary.
- Strong return typing for sync, async, generator, and async-generator factories.
- Reusable `Annotated` dependencies.
- Injected parameters hidden from public runtime signatures.
- Nested-safe dependency overrides.
- A DI-only contract: values pass through unchanged.
- A minimal backend-independent public namespace.

## Versioning

Wireme follows [SemVer](https://semver.org) with the strict 0.x mapping:
below 1.0.0, a breaking change bumps minor and features or fixes bump patch,
so the minor number is the breaking-change signal. Published artifacts are
immutable; a broken release is fixed by publishing a new version. See the
[release notes](https://wireme.mghalix.com/release-notes/).

## License

MIT
