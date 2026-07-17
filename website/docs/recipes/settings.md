# Settings that fail fast

Configuration objects should stop a misconfigured application at startup,
before any request runs, and still be swappable in tests.

```python title="myapp/settings.py"
from typing import Annotated

from pydantic_settings import BaseSettings

from wireme import wired


class Settings(BaseSettings):
    database_url: str
    request_timeout: float = 5.0


settings = Settings()  # (1)!


def get_settings() -> Settings:
    return settings


type SettingsDep = Annotated[Settings, wired(get_settings)]
```

1. Constructing at module scope validates the environment at import time:
   a missing `DATABASE_URL` fails the deployment, not the first request.
   `Settings` owns that validation; Wireme only injects the constructed object.

Every consumer declares the alias and receives the same instance:

```python
@wire
def make_report(*, config: SettingsDep = Wired()) -> str:
    return f"report against {config.database_url}"
```

Tests override the named factory, so the whole graph sees test settings:

```python
def get_test_settings() -> Settings:
    return Settings(database_url="sqlite://:memory:")


with override_dependency(get_settings, get_test_settings):
    make_report()
```

!!! warning "Not `use_cache`, not a lambda"
    `use_cache=True` caches once per wired call, not process-wide, and
    `wired(lambda: settings)` creates a distinct factory per call site that
    overrides cannot target. The named factory over a module instance is
    the whole recipe.

When eager construction is wrong (optional integrations, expensive
clients), swap the module instance for a cached factory:

```python
import functools


@functools.cache
def get_settings() -> Settings:
    return Settings()
```
