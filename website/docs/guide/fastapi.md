# FastAPI integration

Install the optional extra:

```bash
uv add 'wireme[fastapi]'
```

The integration lives in `wireme.fastapi` and exposes two names:

```python
from wireme.fastapi import FromWeb, override_web_dependency
```

Ownership is split deliberately:

- FastAPI owns the request-facing dependency lifecycle.
- FastAPI validates request-facing inputs.
- Wireme owns the internal dependency graph behind constructors and
  factories and passes its values through unchanged.

`import wireme` never requires FastAPI. Importing `wireme.fastapi` without
the extra raises `ModuleNotFoundError` with an actionable message:

```
wireme.fastapi is unavailable because the 'fastapi' extra is not installed. Install it with: uv add 'wireme[fastapi]'
```

## Wired classes

FastAPI constructs the class. Wireme resolves the hidden constructor
dependencies:

```python
from fastapi import FastAPI

from wireme import Wired, wire
from wireme.fastapi import FromWeb


@wire
class UserService:
    def __init__(self, *, database: DatabaseDep = Wired()) -> None:
        self._database = database

    def list_users(self) -> list[str]:
        return self._database.usernames()


app = FastAPI()


@app.get("/users")
def list_users(*, service: FromWeb[UserService]) -> list[str]:
    return service.list_users()
```

## Reusable wired aliases

A Wireme dependency alias can be bridged into FastAPI directly. `FromWeb`
unwraps the PEP 695 alias, finds the `wired()` metadata, and bridges the
factory while preserving the static type, nested dependency resolution,
cache configuration, overrides, and resource lifecycle:

```python
def get_user_service(*, database: DatabaseDep = Wired()) -> UserService:
    return UserService(database=database)


type UserServiceDep = Annotated[
    UserService,
    wired(get_user_service),
]


@app.get("/users")
def list_users(*, service: FromWeb[UserServiceDep]) -> list[str]:
    return service.list_users()
```

All factory forms are supported: sync and async functions, generator and
async-generator functions, callable objects, and `functools.partial`. The
factory must be hashable so its bridge keeps a stable identity for caching
and overrides.

## Request-scoped resources

Generator and async-generator factories follow FastAPI's request lifecycle.
The resource opens when the request resolves it, stays open while the
endpoint runs and the response streams, then closes exactly once. Nested
resources close in reverse order, and endpoint exceptions propagate into
the generator:

```python
def get_connection() -> Iterator[Connection]:
    connection = Connection()
    try:
        yield connection
    finally:
        connection.close()


type ConnectionDep = Annotated[
    Connection,
    wired(get_connection),
]


@app.get("/report")
def report(*, connection: FromWeb[ConnectionDep]) -> dict[str, str]:
    return {"status": connection.status()}
```

## Web overrides

`override_web_dependency()` temporarily replaces a dependency on one
application. It covers direct FastAPI dependencies and bridged Wireme
factories, restores previous state on exit including after exceptions, and
nests correctly:

```python
from wireme.fastapi import override_web_dependency


def get_test_service() -> UserService:
    return UserService(database=TestDatabase())


with override_web_dependency(app, get_user_service, get_test_service):
    client.get("/users")
```

Replacements may be sync, async, generator, or async-generator factories
and may have different parameter lists.

One limitation: bridged adapters are discovered when the override context
is entered, so routes using `FromWeb` must be registered before entering
the context. A `FromWeb` annotation evaluated for the first time inside the
context is only overridden after the context is entered again.

## Wiring endpoints directly

`@wire` also works directly on an endpoint. Apply it under the route
decorator so FastAPI registers the wired function:

```python
@app.get("/users")
@wire
def list_users(limit: int = 10, *, service: UserServiceDep) -> list[str]:
    return service.list_users()[:limit]
```

FastAPI keeps ownership of the visible parameters: `limit` stays a query
parameter and injected parameters stay out of the OpenAPI schema. No
`= Wired()` default is needed because endpoints are never called
explicitly; add it only if other code calls the function directly.

Prefer `FromWeb` as the default integration. Wiring the endpoint trades
away FastAPI's request lifecycle:

- Generator dependencies close when the endpoint returns, before the
  response is sent. Use `FromWeb` for request-scoped resources and
  streaming responses.
- The hidden dependencies are invisible to FastAPI, so replace them with
  `override_dependency()`, not `override_web_dependency()`.

Applying the decorators in the wrong order fails at registration time with
a FastAPI error about the unresolved wired annotation.

## Runnable examples

[examples/fastapi_integration.py](https://github.com/mghalix/wireme/blob/main/examples/fastapi_integration.py),
[examples/fastapi_resources.py](https://github.com/mghalix/wireme/blob/main/examples/fastapi_resources.py),
[examples/fastapi_overrides.py](https://github.com/mghalix/wireme/blob/main/examples/fastapi_overrides.py),
[examples/fastapi_endpoints.py](https://github.com/mghalix/wireme/blob/main/examples/fastapi_endpoints.py)

Next: [Building integrations](extending.md)
