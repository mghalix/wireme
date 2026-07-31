"""Context manager factories as dependencies.

A factory decorated with @contextmanager or @asynccontextmanager behaves
exactly like the generator function it wraps: it is entered before the
wired call and closed afterwards, in reverse order. This is what lets an
existing context manager, such as a database session, be reused as a
dependency without rewriting it as a bare generator.
"""

from __future__ import annotations

import asyncio
import sqlite3
from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager, contextmanager
from typing import Annotated

from wireme import Wired, wire, wired

events: list[str] = []


@contextmanager
def get_connection() -> Generator[sqlite3.Connection]:
    events.append("open connection")
    connection = sqlite3.connect(":memory:")
    try:
        yield connection
    finally:
        connection.close()
        events.append("close connection")


type ConnectionDep = Annotated[
    sqlite3.Connection,
    wired(get_connection),
]


@wire
def count_rows(*, connection: ConnectionDep = Wired()) -> int:
    connection.execute("create table hero (name text)")
    connection.executemany(
        "insert into hero values (?)",
        [("Deadpond",), ("Spider-Boy",)],
    )

    row = connection.execute("select count(*) from hero").fetchone()

    return int(row[0])


class Client:
    async def fetch(self, path: str) -> str:
        return f"response from {path}"


@asynccontextmanager
async def get_client() -> AsyncGenerator[Client]:
    events.append("open client")
    try:
        yield Client()
    finally:
        events.append("close client")


type ClientDep = Annotated[Client, wired(get_client)]


@wire
async def fetch(path: str, *, client: ClientDep = Wired()) -> str:
    return await client.fetch(path)


async def main() -> None:
    assert count_rows() == 2
    assert await fetch("/heroes") == "response from /heroes"
    assert events == [
        "open connection",
        "close connection",
        "open client",
        "close client",
    ]

    print("\n".join(events))


if __name__ == "__main__":
    asyncio.run(main())
