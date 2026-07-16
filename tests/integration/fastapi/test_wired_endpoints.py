from collections.abc import Iterator
from typing import Annotated

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from wireme import Wired, override_dependency, wire, wired

pytestmark = pytest.mark.integration


class Database:
    def __init__(self, name: str = "production") -> None:
        self.name = name


def get_database() -> Database:
    return Database()


type DatabaseDep = Annotated[
    Database,
    wired(get_database),
]


events: list[str] = []


def get_connection() -> Iterator[str]:
    events.append("open")
    try:
        yield "connection"
    finally:
        events.append("close")


type ConnectionDep = Annotated[
    str,
    wired(get_connection),
]


def test_wire_decorated_endpoint_resolves_and_hides_dependencies() -> None:
    app = FastAPI()

    @wire
    def endpoint(
        limit: int = 10,
        database: DatabaseDep = Wired(),
    ) -> dict[str, object]:
        return {"limit": limit, "database": database.name}

    app.add_api_route("/", endpoint, methods=["GET"])

    client = TestClient(app)

    assert client.get("/?limit=5").json() == {"limit": 5, "database": "production"}

    parameters = app.openapi()["paths"]["/"]["get"].get("parameters", [])
    assert [parameter["name"] for parameter in parameters] == ["limit"]


def test_wire_decorated_endpoint_needs_no_wired_default() -> None:
    app = FastAPI()

    @wire
    def endpoint(database: DatabaseDep) -> dict[str, str]:
        return {"database": database.name}

    app.add_api_route("/", endpoint, methods=["GET"])

    response = TestClient(app).get("/")

    assert response.json() == {"database": "production"}


def test_wire_decorated_async_endpoint_resolves_dependencies() -> None:
    app = FastAPI()

    @wire
    async def endpoint(database: DatabaseDep = Wired()) -> dict[str, str]:
        return {"database": database.name}

    app.add_api_route("/", endpoint, methods=["GET"])

    response = TestClient(app).get("/")

    assert response.json() == {"database": "production"}


def test_wire_decorated_endpoint_honors_core_overrides() -> None:
    app = FastAPI()

    @wire
    def endpoint(database: DatabaseDep = Wired()) -> dict[str, str]:
        return {"database": database.name}

    app.add_api_route("/", endpoint, methods=["GET"])

    client = TestClient(app)

    def get_test_database() -> Database:
        return Database("test")

    assert client.get("/").json() == {"database": "production"}

    with override_dependency(get_database, get_test_database):
        assert client.get("/").json() == {"database": "test"}

    assert client.get("/").json() == {"database": "production"}


def test_wire_decorated_endpoint_closes_resources_at_return() -> None:
    events.clear()
    app = FastAPI()

    @wire
    def endpoint(connection: ConnectionDep = Wired()) -> dict[str, str]:
        assert events == ["open"]
        return {"connection": connection}

    app.add_api_route("/", endpoint, methods=["GET"])

    response = TestClient(app).get("/")

    assert response.json() == {"connection": "connection"}
    assert events == ["open", "close"]
