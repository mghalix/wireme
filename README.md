# wireme

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/mghalix/wireme/main/.github/assets/wireme-banner-light.png">
    <img src="https://raw.githubusercontent.com/mghalix/wireme/main/.github/assets/wireme-banner.png" alt="wireme - tiny, typed dependency injection for Python" style="width: 100%; max-width: 880px;">
  </picture>
</p>

<p align="center"><em>Tiny, typed dependency injection for Python.</em></p>

<p align="center">
  <a href="https://github.com/mghalix/wireme/actions/workflows/ci.yml"><img src="https://github.com/mghalix/wireme/actions/workflows/ci.yml/badge.svg?branch=main" alt="CI"></a>
  <a href="https://github.com/mghalix/wireme/actions/workflows/ci.yml"><img src="https://img.shields.io/badge/coverage-100%25-brightgreen" alt="Coverage: 100%"></a>
  <a href="https://pypi.org/project/wireme/"><img src="https://img.shields.io/pypi/v/wireme.svg" alt="PyPI version"></a>
  <a href="https://pypi.org/project/wireme/"><img src="https://img.shields.io/pypi/pyversions/wireme.svg" alt="Supported Python versions"></a>
  <a href="https://github.com/mghalix/wireme/blob/main/LICENSE"><img src="https://img.shields.io/github/license/mghalix/wireme.svg" alt="License"></a>
</p>

---

**Documentation**: [wireme.mghalix.com](https://wireme.mghalix.com)

---

Declare how a dependency is created once, then inject it into functions,
methods, constructors, or FastAPI endpoints without turning the dependency
container into an application framework.

Wireme resolves the graph and touches nothing else. It never validates,
coerces, or serializes arguments, dependency results, or return values.

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

Declare a factory, wire an entry point, and keep the dependency fully typed:

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


create_user("mo")
```

Injected parameters are keyword-only and disappear from the public runtime
signature. Callers see application inputs; Wireme resolves the rest.

Classes wire their constructors, and tests replace factories without
monkeypatching consumers:

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
    service = UserService()
```

The optional FastAPI integration lets FastAPI retain ownership of the request
lifecycle while Wireme resolves the internal graph:

```python
from fastapi import FastAPI

from wireme.fastapi import FromWeb


app = FastAPI()


@app.get("/users")
def list_users(*, service: FromWeb[UserService]) -> list[str]:
    return service.list_users()
```

## Why Wireme

- **Four core names.** `wire`, `wired`, `Wired`, and `override_dependency`.
- **Typed end to end.** Reusable `Annotated` aliases keep declarations and
  static types together.
- **Hidden wiring.** Injected parameters stay out of public signatures,
  editor call hints, and OpenAPI schemas.
- **Complete lifecycles.** Sync, async, generator, and async-generator
  factories compose with deterministic cleanup.
- **Predictable values.** Dependency injection never becomes implicit
  validation or coercion.
- **Clean tests.** Overrides are nested-safe and restored after exceptions.

## Learn more

The [documentation](https://wireme.mghalix.com) contains the full
[guide](https://wireme.mghalix.com/guide/), production
[recipes](https://wireme.mghalix.com/recipes/fastapi-app/), and
[Wireme way](https://wireme.mghalix.com/the-wireme-way/). Every public
capability also has a runnable entry in the
[example index](https://github.com/mghalix/wireme/blob/main/examples/README.md).

## Implementation

Wireme currently uses FastDepends internally for graph execution, caching,
async dispatch, and resource lifecycles. That engine is an implementation
detail: application code uses Wireme's API and does not need to learn or import
FastDepends.

## Versioning

Wireme follows [SemVer](https://semver.org) with the strict 0.x mapping:
below 1.0.0, a breaking change bumps minor and features or fixes bump patch.
Published artifacts are immutable; a broken release is fixed by publishing a
new version. See the [release notes](https://wireme.mghalix.com/release-notes/).

## License

MIT
