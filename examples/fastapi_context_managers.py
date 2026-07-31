"""Context manager factories bridged into FastAPI with FromWeb.

The dependency is declared once with wired(...) and reused in endpoints
through FromWeb. FastAPI owns the request lifecycle: the context manager is
entered when the request needs it and exited after the response finishes.
Tests replace it with override_web_dependency like any other factory.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from typing import Annotated

from fastapi import FastAPI
from fastapi.testclient import TestClient

from wireme import wired
from wireme.fastapi import FromWeb, override_web_dependency

events: list[str] = []


@contextmanager
def get_connection() -> Generator[sqlite3.Connection]:
    events.append("open connection")
    connection = sqlite3.connect(":memory:")
    connection.execute("create table hero (name text)")
    connection.execute("insert into hero values ('Deadpond')")
    try:
        yield connection
    finally:
        connection.close()
        events.append("close connection")


type ConnectionDep = Annotated[
    sqlite3.Connection,
    wired(get_connection),
]


app = FastAPI()


@app.get("/heroes")
def list_heroes(*, connection: FromWeb[ConnectionDep]) -> list[str]:
    events.append("handle request")
    return [name for (name,) in connection.execute("select name from hero")]


client = TestClient(app)

assert client.get("/heroes").json() == ["Deadpond"]
assert events == ["open connection", "handle request", "close connection"]

print("\n".join(events))


@contextmanager
def get_test_connection() -> Generator[sqlite3.Connection]:
    connection = sqlite3.connect(":memory:")
    connection.execute("create table hero (name text)")
    connection.execute("insert into hero values ('Spider-Boy')")
    try:
        yield connection
    finally:
        connection.close()


with override_web_dependency(app, get_connection, get_test_connection):
    assert client.get("/heroes").json() == ["Spider-Boy"]

assert client.get("/heroes").json() == ["Deadpond"]

print("override restored")
