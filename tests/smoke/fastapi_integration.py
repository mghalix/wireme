"""Verify the installed FastAPI integration."""

from __future__ import annotations

import typing
from collections.abc import AsyncIterator, Iterator
from typing import Annotated

from fastapi import FastAPI
from fastapi.testclient import TestClient

from wireme import Wired, wire, wired
from wireme.fastapi import FromWeb

events: list[str] = []


class Database:
    def __init__(self, name: str) -> None:
        self.name = name


def get_database() -> Database:
    return Database("production")


type DatabaseDep = Annotated[
    Database,
    wired(get_database),
]


class Service:
    @wire
    def __init__(self, database: DatabaseDep = Wired()) -> None:
        self.database = database


def get_connection() -> Iterator[Database]:
    events.append("open-sync")
    try:
        yield Database("sync-resource")
    finally:
        events.append("close-sync")


type ConnectionDep = Annotated[
    Database,
    wired(get_connection),
]


async def get_session() -> AsyncIterator[Database]:
    events.append("open-async")
    try:
        yield Database("async-resource")
    finally:
        events.append("close-async")


type SessionDep = Annotated[
    Database,
    wired(get_session),
]


def get_uncoerced_number() -> int:
    return typing.cast("int", "1")


type UncoercedNumberDep = Annotated[
    int,
    wired(get_uncoerced_number),
]


app = FastAPI()


@app.get("/")
def endpoint(service: FromWeb[Service]) -> dict[str, str]:
    return {"database": service.database.name}


@app.get("/sync-resource")
def sync_resource_endpoint(connection: FromWeb[ConnectionDep]) -> dict[str, str]:
    events.append("use-sync")
    return {"database": connection.name}


@app.get("/async-resource")
def async_resource_endpoint(session: FromWeb[SessionDep]) -> dict[str, str]:
    events.append("use-async")
    return {"database": session.name}


@app.get("/uncoerced")
def uncoerced_endpoint(number: FromWeb[UncoercedNumberDep]) -> dict[str, object]:
    return {"number": number, "type": type(number).__name__}


client = TestClient(app)

response = client.get("/")
assert response.status_code == 200
assert response.json() == {"database": "production"}

response = client.get("/sync-resource")
assert response.status_code == 200
assert response.json() == {"database": "sync-resource"}
assert events == ["open-sync", "use-sync", "close-sync"], events

events.clear()

response = client.get("/async-resource")
assert response.status_code == 200
assert response.json() == {"database": "async-resource"}
assert events == ["open-async", "use-async", "close-async"], events

response = client.get("/uncoerced")
assert response.status_code == 200
assert response.json() == {"number": "1", "type": "str"}

print("wireme FastAPI lifecycle and unchanged-value smoke test passed")
