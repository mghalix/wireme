# Resources

Async factories are supported:

```python
async def get_client() -> Client:
    return await Client.connect()


@wire
async def fetch_user(
    user_id: str,
    *,
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

Cleanup runs after the wired callable finishes. Nested resources close in
reverse order. For resources that must stay open for a whole web request,
see the [FastAPI integration](fastapi.md).

## Context managers

A factory decorated with `@contextmanager` or `@asynccontextmanager` works
the same way, so an existing context manager can be reused as a dependency
without rewriting it as a bare generator:

```python
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager


@contextmanager
def get_connection() -> Generator[sqlite3.Connection]:
    connection = sqlite3.connect("app.db")
    try:
        yield connection
    finally:
        connection.close()


type ConnectionDep = Annotated[sqlite3.Connection, wired(get_connection)]
```

`wired(...)` resolves the dependency through the generator function the
decorator wraps, so the static type stays `sqlite3.Connection` rather than
the context manager object. Declaration sites, `override_dependency`, and
`override_web_dependency` all accept the decorated factory.

Only `contextlib`'s two decorators are treated this way. Other decorators
applied with `functools.wraps`, including caches such as
`functools.lru_cache`, stay intact and keep running.

## Runnable examples

[examples/resources.py](https://github.com/mghalix/wireme/blob/main/examples/resources.py)

[examples/context_managers.py](https://github.com/mghalix/wireme/blob/main/examples/context_managers.py)

Next: [Testing](testing.md)
