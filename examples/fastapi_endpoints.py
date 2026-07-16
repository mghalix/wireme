"""Wire a FastAPI endpoint directly with @wire.

Prefer FromWeb as the default integration; wiring the endpoint suits plain
service dependencies without request-lifecycle needs. Apply @wire under the
route decorator so FastAPI registers the wired function.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import FastAPI
from fastapi.testclient import TestClient

from wireme import wire, wired


class Database:
    def __init__(self) -> None:
        self.usernames = ["mo", "sam"]


def get_database() -> Database:
    return Database()


type DatabaseDep = Annotated[
    Database,
    wired(get_database),
]


app = FastAPI()


@app.get("/users")
@wire
def list_users(limit: int = 10, *, database: DatabaseDep) -> list[str]:
    return database.usernames[:limit]


client = TestClient(app)

assert client.get("/users?limit=1").json() == ["mo"]

parameters = app.openapi()["paths"]["/users"]["get"]["parameters"]
assert [parameter["name"] for parameter in parameters] == ["limit"]

print("endpoint wired; injected parameter hidden from OpenAPI")
