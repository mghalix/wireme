# wireme

Tiny, typed dependency injection for Python, powered by FastDepends.

Wireme keeps dependency injection explicit and small:

```python
from wireme import Wired, override_dependency, wire, wired
```

- `@wire` enables dependency resolution for a function or method.
- `wired(factory)` declares how a dependency is created.
- `Wired()` marks a reusable `Annotated` dependency as caller-optional.
- `override_dependency()` temporarily replaces a dependency in tests.

## Installation

```bash
uv add wireme
```

Wireme requires Python 3.12 or newer.

## Quick start

```python
from wireme import wire, wired


class Database:
    def write(self, value: str) -> None:
        print(f"writing: {value}")


def get_database() -> Database:
    return Database()


@wire
def process_text(
    text: str,
    database: Database = wired(get_database),
) -> None:
    database.write(text)


process_text("Hello, world")
```

Callers only provide application inputs. Wireme resolves `database` automatically.
Injected parameters are also removed from the public runtime signature:

```python
import inspect

assert str(inspect.signature(process_text)) == "(text: str) -> None"
```

## Reusable dependencies

Use `Annotated` when the same dependency appears in multiple callables:

```python
from typing import Annotated

from wireme import Wired, wire, wired


type DatabaseDep = Annotated[Database, wired(get_database)]


@wire
def create_user(
    username: str,
    database: DatabaseDep = Wired(),
) -> None:
    database.write(username)


create_user("mo")
```

`wired(get_database)` stores the dependency declaration in the annotation.
`Wired()` tells type checkers and call sites that the argument does not need to be
passed explicitly.

## Wiring classes

Decorate constructors or methods individually. Do not decorate the class itself.

Use constructor injection when the dependency belongs to the object's state:

```python
from typing import Annotated

from wireme import Wired, wire, wired


type DatabaseDep = Annotated[Database, wired(get_database)]


class TextProcessor:
    @wire
    def __init__(self, database: DatabaseDep = Wired()) -> None:
        self._database = database

    def process(self, text: str) -> None:
        self._database.write(text)


TextProcessor().process("Hello from constructor injection")
```

Use method injection when only a specific operation needs the dependency:

```python
class TextProcessor:
    @wire
    def process(
        self,
        text: str,
        database: DatabaseDep = Wired(),
    ) -> None:
        database.write(text)


TextProcessor().process("Hello from method injection")
```

Constructor injection is useful for dependencies shared across multiple methods.
Method injection keeps the object stateless when only one operation needs the
dependency.

See [examples/classes.py](https://github.com/mghalix/wireme/blob/main/examples/classes.py) for a complete runnable example.

## Explicit values take precedence

A caller may still provide a dependency explicitly. The passed value wins over
injection:

```python
class TestDatabase(Database):
    pass


create_user("mo", TestDatabase())
```

This is useful for one-off composition. For test suites, prefer
`override_dependency()` so every nested dependency sees the replacement.

## Test overrides

```python
from wireme import override_dependency


def get_test_database() -> Database:
    return TestDatabase()


with override_dependency(get_database, get_test_database):
    create_user("mo")
```

Overrides are restored when the context exits, including after exceptions.
Nested overrides restore the previous outer override correctly.

The provider is shared at process level. Use overrides for isolated tests and
application setup, not concurrent request-level mutation.

## Nested dependencies and caching

Factories can depend on other factories:

```python
from wireme import wire, wired


def get_settings() -> Settings:
    return Settings()


def get_database(
    settings: Settings = wired(get_settings),
) -> Database:
    return Database(settings.database_url)


@wire
def operation(database: Database = wired(get_database)) -> None:
    ...
```

Dependencies are cached once per wired call by default. Disable caching for a
specific declaration when every use must create a new value:

```python
value: Token = wired(create_token, use_cache=False)
```

## Async and resource dependencies

Async factories are supported:

```python
async def get_client() -> Client:
    return await Client.connect()


@wire
async def fetch_user(
    user_id: str,
    client: Client = wired(get_client),
) -> User:
    return await client.fetch_user(user_id)
```

Generator and async-generator factories can own resource cleanup:

```python
from collections.abc import AsyncIterator


async def get_client() -> AsyncIterator[Client]:
    client = await Client.connect()
    try:
        yield client
    finally:
        await client.close()
```

Cleanup runs after the wired callable finishes.

## Protocol dependencies

A protocol can describe the dependency interface. When runtime validation is
active, make the protocol runtime-checkable:

```python
from typing import Annotated, Protocol, runtime_checkable

from wireme import Wired, wire, wired


@runtime_checkable
class DatabaseLike(Protocol):
    def write(self, value: str) -> None: ...


type DatabaseDep = Annotated[DatabaseLike, wired(get_database)]


@wire
def process(
    value: str,
    database: DatabaseDep = Wired(),
) -> None:
    database.write(value)
```

## Build integrations on top of Wireme

Wireme can be the small DI primitive behind a project-specific API. For example,
a service or plugin registry can expose `wired_service(ServiceType)` while still
using Wireme for resolution, typing, caching, and overrides.

```python
import functools

from collections.abc import Callable
from typing import cast

from wireme import WiremeError, wired


class ServiceUnavailableError(WiremeError):
    pass


_services: dict[type[object], object] = {}


@functools.cache
def require_service[T](service_type: type[T]) -> Callable[[], T]:
    def dependency() -> T:
        try:
            service = _services[service_type]
        except KeyError as error:
            raise ServiceUnavailableError(
                f"{service_type.__name__} is not registered."
            ) from error

        return cast(T, service)

    return dependency


def wired_service[T](service_type: type[T]) -> T:
    return wired(require_service(service_type))
```

Caching the generated factory gives it stable identity, which is important when
using `override_dependency()`.

See [`examples/custom_integration.py`](https://github.com/mghalix/wireme/blob/main/examples/custom_integration.py) for a
complete runnable example.

## Errors

Wireme exposes:

```python
from wireme import ValidationError, WiremeError
```

- `WiremeError` is the base error exposed by Wireme.
- `ValidationError` represents dependency input or result validation failures.

Project-specific DI errors may inherit from `WiremeError`.

## Ruff configuration

Ruff's `B008` rule normally rejects function calls in defaults. Tell Ruff that
`Wired()` is an immutable marker:

```toml
[tool.ruff.lint.flake8-bugbear]
extend-immutable-calls = ["wireme.Wired"]
```

Declarations using `wired(factory)` may also need your project's normal DI rule
configuration, depending on which Ruff rules are enabled.

## Public API

| Name                  | Purpose                                                         |
| --------------------- | --------------------------------------------------------------- |
| `wire`                | Decorate a function or method and enable dependency resolution. |
| `wired`               | Declare a dependency factory and its resolution options.        |
| `Wired`               | Mark an `Annotated` dependency as caller-optional.              |
| `override_dependency` | Temporarily replace a factory, with nested restoration.         |
| `WiremeError`         | Base error exposed by Wireme.                                   |
| `ValidationError`     | Dependency validation error.                                    |

## Examples

- [`examples/basic.py`](https://github.com/mghalix/wireme/blob/main/examples/basic.py) covers direct and reusable dependencies.
- [`examples/classes.py`](https://github.com/mghalix/wireme/blob/main/examples/classes.py) covers constructor and method injection.
- [`examples/overrides.py`](https://github.com/mghalix/wireme/blob/main/examples/overrides.py) covers isolated test overrides.
- [`examples/protocols.py`](https://github.com/mghalix/wireme/blob/main/examples/protocols.py) covers interface-based dependencies.
- [`examples/resources.py`](https://github.com/mghalix/wireme/blob/main/examples/resources.py) covers async resource cleanup.
- [`examples/custom_integration.py`](https://github.com/mghalix/wireme/blob/main/examples/custom_integration.py) builds a typed service registry integration.

Run any example with:

```bash
uv run python examples/basic.py
```

## Why Wireme instead of importing FastDepends directly?

FastDepends provides the resolution engine. Wireme provides a deliberately small,
opinionated facade with:

- A cohesive `wire`, `wired`, and `Wired` vocabulary.
- Strong return typing for sync, async, generator, and async-generator factories.
- Reusable `Annotated` dependencies.
- Injected parameters hidden from public runtime signatures.
- Nested-safe dependency overrides.
- A minimal backend-independent public namespace.

## License

MIT
