from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from wireme import wire, wired


class Client:
    @classmethod
    async def connect(cls) -> Client:
        print("client connected")
        return cls()

    async def fetch(self, path: str) -> str:
        return f"response from {path}"

    async def close(self) -> None:
        print("client closed")


async def get_client() -> AsyncIterator[Client]:
    client = await Client.connect()
    try:
        yield client
    finally:
        await client.close()


@wire
async def fetch(
    path: str,
    client: Client = wired(get_client),
) -> str:
    return await client.fetch(path)


async def main() -> None:
    print(await fetch("/users/mo"))


if __name__ == "__main__":
    asyncio.run(main())
