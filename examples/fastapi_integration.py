"""FromWeb with a wired class and a wired alias, plus a web override.

FastAPI owns the request-facing dependency lifecycle. Wireme resolves the
internal dependency graph behind constructors and factories.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import FastAPI
from fastapi.testclient import TestClient

from wireme import Wired, wire, wired
from wireme.fastapi import FromWeb, override_web_dependency


class Database:
    def __init__(self, name: str = "production") -> None:
        self.name = name


def get_database() -> Database:
    return Database()


type DatabaseDep = Annotated[
    Database,
    wired(get_database),
]


@wire
class UserService:
    def __init__(
        self,
        *,
        database: DatabaseDep = Wired(),
    ) -> None:
        self._database = database

    def describe(self) -> str:
        return f"Using {self._database.name}"


def get_user_service(
    *,
    database: DatabaseDep = Wired(),
) -> UserService:
    return UserService(database=database)


type UserServiceDep = Annotated[
    UserService,
    wired(get_user_service),
]


app = FastAPI()


@app.get("/constructed")
def constructed(service: FromWeb[UserService]) -> dict[str, str]:
    return {"message": service.describe()}


@app.get("/bridged")
def bridged(service: FromWeb[UserServiceDep]) -> dict[str, str]:
    return {"message": service.describe()}


client = TestClient(app)

assert client.get("/constructed").json() == {"message": "Using production"}
assert client.get("/bridged").json() == {"message": "Using production"}


def get_test_service() -> UserService:
    return UserService(database=Database("test"))


with override_web_dependency(app, UserService, get_test_service):
    assert client.get("/constructed").json() == {"message": "Using test"}

with override_web_dependency(app, get_user_service, get_test_service):
    assert client.get("/bridged").json() == {"message": "Using test"}

assert client.get("/constructed").json() == {"message": "Using production"}
assert client.get("/bridged").json() == {"message": "Using production"}

print("FromWeb wired class, wired alias, and overrides work")
