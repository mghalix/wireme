from __future__ import annotations

import dataclasses
import typing
from typing import Annotated

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from wireme import wired
from wireme.fastapi import FromWeb

from ._support import (
    AsyncUserServiceDep,
    ClassWiredService,
    Database,
    PlainService,
    UserServiceDep,
    WiredService,
    get_database,
)

pytestmark = pytest.mark.integration


def get_uncoerced_number() -> int:
    return typing.cast("int", "1")


type UncoercedNumberDep = Annotated[int, wired(get_uncoerced_number)]


def test_from_web_constructs_plain_class() -> None:
    app = FastAPI()

    def endpoint(
        service: FromWeb[PlainService],
    ) -> dict[str, str]:
        return {"name": service.name}

    app.add_api_route(
        "/",
        endpoint,
        methods=["GET"],
    )

    response = TestClient(app).get("/")

    assert response.status_code == 200, response.text
    assert response.json() == {
        "name": "plain",
    }


def test_from_web_constructs_wired_class() -> None:
    app = FastAPI()

    def endpoint(
        service: FromWeb[WiredService],
    ) -> dict[str, str]:
        return {"database": service.database.name}

    app.add_api_route(
        "/",
        endpoint,
        methods=["GET"],
    )

    response = TestClient(app).get("/")

    assert response.status_code == 200, response.text
    assert response.json() == {
        "database": "production",
    }


def test_from_web_constructs_class_decorated_service() -> None:
    app = FastAPI()

    def endpoint(
        service: FromWeb[ClassWiredService],
    ) -> dict[str, str]:
        return {"database": service.database.name}

    app.add_api_route(
        "/",
        endpoint,
        methods=["GET"],
    )

    response = TestClient(app).get("/")

    assert response.status_code == 200, response.text
    assert response.json() == {
        "database": "production",
    }


def test_from_web_bridges_wired_alias() -> None:
    app = FastAPI()

    def endpoint(
        service: FromWeb[UserServiceDep],
    ) -> dict[str, str]:
        return {"database": service.database.name}

    app.add_api_route(
        "/",
        endpoint,
        methods=["GET"],
    )

    response = TestClient(app).get("/")

    assert response.status_code == 200, response.text
    assert response.json() == {
        "database": "production",
    }


def test_from_web_bridges_async_factory() -> None:
    app = FastAPI()

    def endpoint(
        service: FromWeb[AsyncUserServiceDep],
    ) -> dict[str, str]:
        return {"database": service.database.name}

    app.add_api_route(
        "/",
        endpoint,
        methods=["GET"],
    )

    response = TestClient(app).get("/")

    assert response.status_code == 200, response.text
    assert response.json() == {
        "database": "production",
    }


def test_from_web_bridge_preserves_factory_results() -> None:
    app = FastAPI()

    def endpoint(number: FromWeb[UncoercedNumberDep]) -> dict[str, object]:
        return {"number": number, "type": type(number).__name__}

    app.add_api_route("/", endpoint, methods=["GET"])

    response = TestClient(app).get("/")

    assert response.status_code == 200, response.text
    assert response.json() == {"number": "1", "type": "str"}


def test_annotated_alias_without_wired_metadata_is_rejected() -> None:
    invalid_dep = Annotated[str, "not-wireme-metadata"]

    with pytest.raises(
        TypeError,
        match=r"does not contain wired",
    ):
        _ = FromWeb[invalid_dep]


def test_multiple_wired_metadata_entries_are_rejected() -> None:
    first = wired(get_database)
    second = wired(get_database)

    invalid_dep = Annotated[
        Database,
        first,
        second,
    ]

    with pytest.raises(
        TypeError,
        match=r"exactly one wired",
    ):
        _ = FromWeb[invalid_dep]


def test_unhashable_factory_is_rejected() -> None:
    @dataclasses.dataclass
    class DatabaseFactory:
        name: str

        def __call__(self) -> Database:
            return Database(self.name)

    factory = DatabaseFactory("production")

    database_dep = Annotated[
        Database,
        wired(factory),
    ]

    with pytest.raises(
        TypeError,
        match=r"factories must be hashable",
    ):
        _ = FromWeb[database_dep]
