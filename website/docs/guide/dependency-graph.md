# The dependency graph

## Nested dependencies

Factories can depend on other factories:

```python
from wireme import wire, wired


def get_settings() -> Settings:
    return Settings()


def get_database(
    *,
    settings: Settings = wired(get_settings),
) -> Database:
    return Database(settings.database_url)


@wire
def operation(*, database: Database = wired(get_database)) -> None:
    ...
```

## Per-call caching

Dependencies are cached once per wired call by default: when several
factories share a dependency, it resolves once for the whole call. Disable
caching for a specific declaration when every use must create a new value:

```python
value: Token = wired(create_token, use_cache=False)
```

## Singletons

`use_cache=True` caches once per wired call, not process-wide. A singleton
is a module-level instance exposed through a named factory:

```python
settings = Settings()  # validates configuration once, at import time


def get_settings() -> Settings:
    return settings


type SettingsDep = Annotated[Settings, wired(get_settings)]
```

Creating the instance at module scope fails fast: a misconfigured
environment stops the application at import, before any request runs. This
fits pydantic settings and similar validate-on-construction objects.

When lazy creation is acceptable, cache the factory instead and drop the
module-level instance:

```python
import functools


@functools.cache
def get_settings() -> Settings:
    return Settings()
```

Either way the factory is a named module-level function, so
`override_dependency(get_settings, get_test_settings)` can target it.

Avoid `wired(lambda: settings)`. Each `wired(lambda: ...)` call site creates
a distinct factory object, so overrides cannot target the dependency and
error messages lose the factory name.

## Factory forms

A factory is anything callable. All of these inject:

- functions, sync or async, plain or generator
- classes: the constructor runs and the instance is injected
- pre-built callable instances
- staticmethods and bound methods
- `functools.partial`

Factories may also consume the caller's arguments by name, so one incoming
value can feed both the entry point and its dependencies:

```python
@wire
def migrate(dsn: str, *, repository: RepositoryDep = Wired()) -> str:
    ...  # Repository(dsn) was built from the same dsn argument
```

## Runnable examples

[examples/nested.py](https://github.com/mghalix/wireme/blob/main/examples/nested.py),
[examples/singletons.py](https://github.com/mghalix/wireme/blob/main/examples/singletons.py),
[examples/factories.py](https://github.com/mghalix/wireme/blob/main/examples/factories.py)

Next: [Resources](resources.md)
