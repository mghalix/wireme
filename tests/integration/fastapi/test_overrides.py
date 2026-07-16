from collections.abc import AsyncIterator, Iterator
from typing import Annotated

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from wireme import wired
from wireme.fastapi import FromWeb, override_web_dependency

from ._support import (
    Database,
    DirectValueDep,
    UserService,
    UserServiceDep,
    get_direct_value,
    get_inner_user_service,
    get_outer_user_service,
    get_test_direct_value,
    get_test_user_service,
    get_user_service,
)

pytestmark = pytest.mark.integration


def get_fresh_value() -> str:
    return "original"


def get_replacement_value() -> str:
    return "replacement"


type FreshValueDep = Annotated[
    str,
    wired(get_fresh_value),
]


def _create_bridged_app() -> FastAPI:
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

    return app


def test_override_web_dependency() -> None:
    app = _create_bridged_app()
    client = TestClient(app)

    assert client.get("/").json() == {
        "database": "production",
    }

    with override_web_dependency(
        app,
        get_user_service,
        get_test_user_service,
    ):
        assert client.get("/").json() == {
            "database": "test",
        }

    assert client.get("/").json() == {
        "database": "production",
    }


def test_nested_web_overrides_restore_outer_override() -> None:
    app = _create_bridged_app()
    client = TestClient(app)

    with override_web_dependency(
        app,
        get_user_service,
        get_outer_user_service,
    ):
        assert client.get("/").json() == {
            "database": "outer",
        }

        with override_web_dependency(
            app,
            get_user_service,
            get_inner_user_service,
        ):
            assert client.get("/").json() == {
                "database": "inner",
            }

        assert client.get("/").json() == {
            "database": "outer",
        }

    assert client.get("/").json() == {
        "database": "production",
    }


def test_web_override_is_restored_after_exception() -> None:
    app = _create_bridged_app()
    client = TestClient(app)

    with (
        pytest.raises(RuntimeError, match="boom"),
        override_web_dependency(
            app,
            get_user_service,
            get_test_user_service,
        ),
    ):
        assert client.get("/").json() == {
            "database": "test",
        }

        raise RuntimeError("boom")

    assert client.get("/").json() == {
        "database": "production",
    }


def test_direct_fastapi_dependency_is_overridden() -> None:
    app = FastAPI()

    def endpoint(
        value: DirectValueDep,
    ) -> dict[str, str]:
        return {"value": value}

    app.add_api_route(
        "/",
        endpoint,
        methods=["GET"],
    )

    client = TestClient(app)

    assert client.get("/").json() == {
        "value": "production:value",
    }

    with override_web_dependency(
        app,
        get_direct_value,
        get_test_direct_value,
    ):
        assert client.get("/").json() == {
            "value": "test:value",
        }

    assert client.get("/").json() == {
        "value": "production:value",
    }


def test_generator_replacement_is_cleaned_up() -> None:
    app = _create_bridged_app()
    client = TestClient(app)
    events: list[str] = []

    def get_generator_service() -> Iterator[UserService]:
        events.append("open")
        try:
            yield UserService(Database("generator"))
        finally:
            events.append("close")

    with override_web_dependency(
        app,
        get_user_service,
        get_generator_service,
    ):
        assert client.get("/").json() == {
            "database": "generator",
        }

    assert events == ["open", "close"]
    assert client.get("/").json() == {
        "database": "production",
    }


def test_async_generator_replacement_is_cleaned_up() -> None:
    app = _create_bridged_app()
    client = TestClient(app)
    events: list[str] = []

    async def get_async_generator_service() -> AsyncIterator[UserService]:
        events.append("open")
        try:
            yield UserService(Database("async-generator"))
        finally:
            events.append("close")

    with override_web_dependency(
        app,
        get_user_service,
        get_async_generator_service,
    ):
        assert client.get("/").json() == {
            "database": "async-generator",
        }

    assert events == ["open", "close"]
    assert client.get("/").json() == {
        "database": "production",
    }


def test_bridges_created_inside_override_context_need_reentry() -> None:
    app = FastAPI()
    client = TestClient(app)

    with override_web_dependency(
        app,
        get_fresh_value,
        get_replacement_value,
    ):

        def endpoint(value: FromWeb[FreshValueDep]) -> dict[str, str]:
            return {"value": value}

        app.add_api_route("/", endpoint, methods=["GET"])

        assert client.get("/").json() == {
            "value": "original",
        }

    with override_web_dependency(
        app,
        get_fresh_value,
        get_replacement_value,
    ):
        assert client.get("/").json() == {
            "value": "replacement",
        }
