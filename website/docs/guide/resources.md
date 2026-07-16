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

## Runnable example

[examples/resources.py](https://github.com/mghalix/wireme/blob/main/examples/resources.py)

Next: [Testing](testing.md)
