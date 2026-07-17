"""Nested-safe FastAPI dependency overrides with override_web_dependency.

Overrides apply to direct FastAPI dependencies and to Wireme factories
bridged by FromWeb. Nested contexts restore the outer override, and the
original state returns when the last context exits.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import FastAPI
from fastapi.testclient import TestClient

from wireme import Wired, wired
from wireme.fastapi import FromWeb, override_web_dependency


class Database:
    def __init__(self, name: str) -> None:
        self.name = name


def get_database() -> Database:
    return Database("production")


type DatabaseDep = Annotated[
    Database,
    wired(get_database),
]


class UserService:
    def __init__(self, database: Database) -> None:
        self.database = database


def get_user_service(
    *,
    database: DatabaseDep = Wired(),
) -> UserService:
    return UserService(database)


type UserServiceDep = Annotated[
    UserService,
    wired(get_user_service),
]


app = FastAPI()


@app.get("/")
def read_service(*, service: FromWeb[UserServiceDep]) -> dict[str, str]:
    return {"database": service.database.name}


def get_staging_service() -> UserService:
    return UserService(Database("staging"))


def get_test_service() -> UserService:
    return UserService(Database("test"))


client = TestClient(app)

assert client.get("/").json() == {"database": "production"}

with override_web_dependency(app, get_user_service, get_staging_service):
    assert client.get("/").json() == {"database": "staging"}

    with override_web_dependency(app, get_user_service, get_test_service):
        assert client.get("/").json() == {"database": "test"}

    assert client.get("/").json() == {"database": "staging"}

assert client.get("/").json() == {"database": "production"}

print("overrides applied and restored correctly")
