import functools
from collections.abc import AsyncIterator, Callable, Iterator
from typing import Annotated, Any

import pytest
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.testclient import TestClient

from wireme import Wired, wired
from wireme.fastapi import FromWeb

pytestmark = pytest.mark.integration

events: list[str] = []


class Connection:
    def __init__(self, name: str) -> None:
        self.name = name


class Session:
    def __init__(self, connection: Connection) -> None:
        self.connection = connection


def get_generator_connection() -> Iterator[Connection]:
    events.append("open")
    try:
        yield Connection("generator")
    finally:
        events.append("close")


type GeneratorConnectionDep = Annotated[
    Connection,
    wired(get_generator_connection),
]


async def get_async_generator_connection() -> AsyncIterator[Connection]:
    events.append("open")
    try:
        yield Connection("async-generator")
    finally:
        events.append("close")


type AsyncGeneratorConnectionDep = Annotated[
    Connection,
    wired(get_async_generator_connection),
]


class CallableConnectionFactory:
    def __call__(self) -> Iterator[Connection]:
        events.append("open")
        try:
            yield Connection("callable")
        finally:
            events.append("close")


type CallableConnectionDep = Annotated[
    Connection,
    wired(CallableConnectionFactory()),
]


class CallableAsyncConnectionFactory:
    async def __call__(self) -> AsyncIterator[Connection]:
        events.append("open")
        try:
            yield Connection("async-callable")
        finally:
            events.append("close")


type CallableAsyncConnectionDep = Annotated[
    Connection,
    wired(CallableAsyncConnectionFactory()),
]


def make_connection(name: str) -> Iterator[Connection]:
    events.append("open")
    try:
        yield Connection(name)
    finally:
        events.append("close")


type PartialConnectionDep = Annotated[
    Connection,
    wired(functools.partial(make_connection, "partial")),
]


def get_observing_connection() -> Iterator[Connection]:
    try:
        yield Connection("observing")
    except RuntimeError as error:
        events.append(f"caught:{error}")
        raise


type ObservingConnectionDep = Annotated[
    Connection,
    wired(get_observing_connection),
]


def get_failing_session(
    connection: GeneratorConnectionDep = Wired(),
) -> Iterator[Session]:
    events.append("fail")
    yield from ()
    raise RuntimeError("session failed")


type FailingSessionDep = Annotated[
    Session,
    wired(get_failing_session),
]


async def get_nested_session(
    connection: GeneratorConnectionDep = Wired(),
) -> AsyncIterator[Session]:
    events.append("open-session")
    try:
        yield Session(connection)
    finally:
        events.append("close-session")


type NestedSessionDep = Annotated[
    Session,
    wired(get_nested_session),
]


def get_chunks() -> Iterator[list[str]]:
    events.append("open")
    try:
        yield ["first", "second"]
    finally:
        events.append("close")


type ChunksDep = Annotated[
    list[str],
    wired(get_chunks),
]


def get_cached_value() -> str:
    events.append("resolve")
    return "value"


type CachedValueDep = Annotated[
    str,
    wired(get_cached_value),
]


def get_fresh_value() -> int:
    events.append("resolve")
    return len(events)


type FreshValueDep = Annotated[
    int,
    wired(get_fresh_value, use_cache=False),
]


def _create_app(endpoint: Callable[..., Any]) -> TestClient:
    events.clear()
    app = FastAPI()
    app.add_api_route("/", endpoint, methods=["GET"])
    return TestClient(app)


def test_generator_factory_cleans_up_after_response() -> None:
    def endpoint(connection: FromWeb[GeneratorConnectionDep]) -> dict[str, str]:
        events.append("use")
        return {"name": connection.name}

    client = _create_app(endpoint)

    response = client.get("/")

    assert response.json() == {"name": "generator"}
    assert events == ["open", "use", "close"]


def test_async_generator_factory_cleans_up_after_response() -> None:
    def endpoint(connection: FromWeb[AsyncGeneratorConnectionDep]) -> dict[str, str]:
        events.append("use")
        return {"name": connection.name}

    client = _create_app(endpoint)

    response = client.get("/")

    assert response.json() == {"name": "async-generator"}
    assert events == ["open", "use", "close"]


def test_callable_generator_object_factory() -> None:
    def endpoint(connection: FromWeb[CallableConnectionDep]) -> dict[str, str]:
        return {"name": connection.name}

    client = _create_app(endpoint)

    response = client.get("/")

    assert response.json() == {"name": "callable"}
    assert events == ["open", "close"]


def test_callable_async_generator_object_factory() -> None:
    def endpoint(connection: FromWeb[CallableAsyncConnectionDep]) -> dict[str, str]:
        return {"name": connection.name}

    client = _create_app(endpoint)

    response = client.get("/")

    assert response.json() == {"name": "async-callable"}
    assert events == ["open", "close"]


def test_functools_partial_generator_factory() -> None:
    def endpoint(connection: FromWeb[PartialConnectionDep]) -> dict[str, str]:
        return {"name": connection.name}

    client = _create_app(endpoint)

    response = client.get("/")

    assert response.json() == {"name": "partial"}
    assert events == ["open", "close"]


def test_cleanup_runs_once_after_endpoint_exception() -> None:
    def endpoint(connection: FromWeb[GeneratorConnectionDep]) -> dict[str, str]:
        raise RuntimeError("boom")

    client = _create_app(endpoint)

    with pytest.raises(RuntimeError, match="boom"):
        client.get("/")

    assert events == ["open", "close"]


def test_endpoint_exception_propagates_into_generator() -> None:
    def endpoint(connection: FromWeb[ObservingConnectionDep]) -> dict[str, str]:
        raise RuntimeError("boom")

    client = _create_app(endpoint)

    with pytest.raises(RuntimeError, match="boom"):
        client.get("/")

    assert events == ["caught:boom"]


def test_nested_resources_close_after_dependency_exception() -> None:
    def endpoint(session: FromWeb[FailingSessionDep]) -> dict[str, str]:
        return {"name": session.connection.name}

    client = _create_app(endpoint)

    with pytest.raises(RuntimeError, match="session failed"):
        client.get("/")

    assert events == ["open", "fail", "close"]


def test_nested_generators_close_in_reverse_order() -> None:
    def endpoint(session: FromWeb[NestedSessionDep]) -> dict[str, str]:
        events.append("use")
        return {"name": session.connection.name}

    client = _create_app(endpoint)

    response = client.get("/")

    assert response.json() == {"name": "generator"}
    assert events == [
        "open",
        "open-session",
        "use",
        "close-session",
        "close",
    ]


def test_resource_stays_open_while_response_is_streaming() -> None:
    def endpoint(chunks: FromWeb[ChunksDep]) -> StreamingResponse:
        def stream() -> Iterator[str]:
            for chunk in chunks:
                events.append(f"stream:{chunk}")
                yield chunk

        return StreamingResponse(stream(), media_type="text/plain")

    client = _create_app(endpoint)

    response = client.get("/")

    assert response.text == "firstsecond"
    assert events == ["open", "stream:first", "stream:second", "close"]


def test_use_cache_true_resolves_once_per_request() -> None:
    def endpoint(
        first: FromWeb[CachedValueDep],
        second: FromWeb[CachedValueDep],
    ) -> dict[str, int]:
        assert first == second
        return {"resolutions": events.count("resolve")}

    client = _create_app(endpoint)

    assert client.get("/").json() == {"resolutions": 1}
    assert client.get("/").json() == {"resolutions": 2}


def test_use_cache_false_resolves_separately() -> None:
    def endpoint(
        first: FromWeb[FreshValueDep],
        second: FromWeb[FreshValueDep],
    ) -> dict[str, int]:
        return {"first": first, "second": second}

    client = _create_app(endpoint)

    response = client.get("/")

    assert response.json() == {"first": 1, "second": 2}
