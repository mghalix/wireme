---
title: Wireme
social_preview: true
hide:
  - toc
---

# Wireme { .hidden }

<p align="center">
  <img class="banner-dark" src="assets/wireme-banner.png" alt="Wireme" style="width: 100%; max-width: 880px; border-radius: 12px;">
  <img class="banner-light" src="assets/wireme-banner-light.png" alt="Wireme" style="width: 100%; max-width: 880px; border-radius: 12px;">
</p>

<p align="center"><strong>Tiny, typed dependency injection for Python.</strong></p>

<p align="center">
Powered by FastDepends. Explicit, opinionated, and small enough to learn in
an afternoon: four names cover the whole core.
</p>

---

Declare how a dependency is created once, then let every function, method,
constructor, or FastAPI endpoint receive it automatically. Injected
parameters disappear from public signatures, stay fully typed, and swap
cleanly in tests.

```python
from typing import Annotated

from wireme import Wired, wire, wired


class Database:
    def write(self, value: str) -> None: ...


def get_database() -> Database:
    return Database()


type DatabaseDep = Annotated[Database, wired(get_database)]


@wire
def create_user(username: str, *, database: DatabaseDep = Wired()) -> None:
    database.write(username)


create_user("mo")  # database is resolved automatically
```

## Install

=== "uv"

    ```bash
    uv add wireme              # framework-independent core
    uv add 'wireme[fastapi]'   # + the FastAPI integration
    ```

=== "pip"

    ```bash
    pip install wireme
    pip install 'wireme[fastapi]'
    ```

Wireme requires Python 3.12 or newer.

New here? Start with [Getting started](guide/getting-started.md), skim
[The Wireme way](the-wireme-way.md) for the house style, or jump into the
[recipes](recipes/fastapi-app.md).

## Highlights

- **Four names.** `wire`, `wired`, `Wired`, `override_dependency` cover the
  core; the optional FastAPI integration adds `FromWeb` and
  `override_web_dependency`. Nothing else to memorize.
- **Typed end to end.** PEP 695 `type` aliases carry the dependency and the
  static type together; BasedPyright strict passes on every example.
- **Hidden wiring.** Injected parameters vanish from runtime signatures, so
  editors, `help()`, and OpenAPI schemas see only real inputs.
- **Validation for free.** Any pydantic annotation constrains a parameter,
  no `BaseModel` or `TypeAdapter` needed for one value.
- **Real lifecycles.** Generator factories open and close resources around
  the call, or around the whole request under FastAPI, including streaming.
- **Test-first overrides.** Nested-safe, exception-safe factory replacement
  for the core and for FastAPI apps.

## Ownership, split deliberately

FastAPI owns the request-facing dependency lifecycle. Wireme owns the
internal dependency graph behind your constructors and factories. `FromWeb`
bridges the two without either side losing its semantics:

```python
from fastapi import FastAPI

from wireme.fastapi import FromWeb


app = FastAPI()


@app.post("/users/{username}")
def create_user(username: str, database: FromWeb[DatabaseDep]) -> None:
    database.write(username)
```

Every capability has a small runnable example in the
[example index](https://github.com/mghalix/wireme/blob/main/examples/README.md),
and every design decision has an
[architecture decision record](https://github.com/mghalix/wireme/blob/main/docs/adr/README.md).
