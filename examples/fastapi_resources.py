"""Request-scoped resources bridged into FastAPI with FromWeb.

FastAPI owns the request lifecycle: resources open when the request needs
them, stay open while the endpoint and response run, and close in reverse
order after the response finishes.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from typing import Annotated

from fastapi import FastAPI
from fastapi.testclient import TestClient

from wireme import Wired, wired
from wireme.fastapi import FromWeb

events: list[str] = []


class Connection:
    def __init__(self, name: str) -> None:
        self.name = name


def get_connection() -> Iterator[Connection]:
    events.append("open connection")
    try:
        yield Connection("primary")
    finally:
        events.append("close connection")


type ConnectionDep = Annotated[
    Connection,
    wired(get_connection),
]


class Session:
    def __init__(self, connection: Connection) -> None:
        self.connection = connection


async def get_session(
    *,
    connection: ConnectionDep = Wired(),
) -> AsyncIterator[Session]:
    events.append("open session")
    try:
        yield Session(connection)
    finally:
        events.append("close session")


type SessionDep = Annotated[
    Session,
    wired(get_session),
]


app = FastAPI()


@app.get("/")
def read_session(session: FromWeb[SessionDep]) -> dict[str, str]:
    events.append("handle request")
    return {"connection": session.connection.name}


client = TestClient(app)

assert client.get("/").json() == {"connection": "primary"}
assert events == [
    "open connection",
    "open session",
    "handle request",
    "close session",
    "close connection",
]

print("\n".join(events))
