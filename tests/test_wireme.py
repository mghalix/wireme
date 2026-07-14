from __future__ import annotations

import inspect
from collections.abc import AsyncGenerator, Generator
from typing import Annotated

import pytest

from wireme import Wired, override_dependency, wire, wired


def get_database() -> str:
    return "production"


Database = Annotated[str, wired(get_database)]


def test_direct_dependency_is_injected_and_hidden() -> None:
    @wire
    def operation(value: int, database: str = wired(get_database)) -> tuple[int, str]:
        return value, database

    assert operation(1) == (1, "production")
    assert tuple(inspect.signature(operation).parameters) == ("value",)


def test_annotated_dependency_is_injected_and_hidden() -> None:
    @wire
    def operation(value: int, database: Database = Wired()) -> tuple[int, str]:
        return value, database

    assert operation(1) == (1, "production")
    assert tuple(inspect.signature(operation).parameters) == ("value",)


def test_nested_dependencies_are_resolved_once_per_call() -> None:
    calls = 0

    def get_number() -> int:
        nonlocal calls
        calls += 1
        return 2

    def get_total(
        first: int = wired(get_number),
        second: int = wired(get_number),
    ) -> int:
        return first + second

    @wire
    def operation(total: int = wired(get_total)) -> int:
        return total

    assert operation() == 4
    assert calls == 1


def test_cache_can_be_disabled() -> None:
    calls = 0

    def get_number() -> int:
        nonlocal calls
        calls += 1
        return calls

    @wire
    def operation(
        first: int = wired(get_number, use_cache=False),
        second: int = wired(get_number, use_cache=False),
    ) -> tuple[int, int]:
        return first, second

    assert operation() == (1, 2)


@pytest.mark.anyio
async def test_async_dependency() -> None:
    async def get_value() -> str:
        return "async"

    @wire
    async def operation(value: str = wired(get_value)) -> str:
        return value

    assert await operation() == "async"


def test_generator_dependency_cleanup() -> None:
    events: list[str] = []

    def get_resource() -> Generator[str, None, None]:
        events.append("open")
        try:
            yield "resource"
        finally:
            events.append("close")

    @wire
    def operation(resource: str = wired(get_resource)) -> str:
        events.append("use")
        return resource

    assert operation() == "resource"
    assert events == ["open", "use", "close"]


@pytest.mark.anyio
async def test_async_generator_dependency_cleanup() -> None:
    events: list[str] = []

    async def get_resource() -> AsyncGenerator[str, None]:
        events.append("open")
        try:
            yield "resource"
        finally:
            events.append("close")

    @wire
    async def operation(resource: str = wired(get_resource)) -> str:
        events.append("use")
        return resource

    assert await operation() == "resource"
    assert events == ["open", "use", "close"]


def test_override_dependency() -> None:
    def get_test_database() -> str:
        return "test"

    @wire
    def operation(database: Database = Wired()) -> str:
        return database

    with override_dependency(get_database, get_test_database):
        assert operation() == "test"

    assert operation() == "production"


def test_nested_overrides_restore_outer_override() -> None:
    def get_outer_database() -> str:
        return "outer"

    def get_inner_database() -> str:
        return "inner"

    @wire
    def operation(database: Database = Wired()) -> str:
        return database

    with override_dependency(get_database, get_outer_database):
        assert operation() == "outer"

        with override_dependency(get_database, get_inner_database):
            assert operation() == "inner"

        assert operation() == "outer"

    assert operation() == "production"


def test_override_is_restored_after_exception() -> None:
    def get_test_database() -> str:
        return "test"

    @wire
    def operation(database: Database = Wired()) -> str:
        return database

    with (
        pytest.raises(RuntimeError, match="boom"),
        override_dependency(get_database, get_test_database),
    ):
        assert operation() == "test"
        raise RuntimeError("boom")

    assert operation() == "production"


def test_method_with_unresolved_class_forward_reference() -> None:
    class Service:
        @wire
        def operation(
            self,
            database: Database = Wired(),
            parent: Service | None = None,
        ) -> str:
            assert parent is None
            return database

    service = Service()

    assert service.operation() == "production"

    signature = inspect.signature(Service.operation)

    assert tuple(signature.parameters) == ("self", "parent")
    assert signature.parameters["parent"].annotation == "Service | None"


def test_override_dependency_accepts_different_signatures() -> None:
    def get_value(prefix: str = "prod") -> str:
        return f"{prefix}:value"

    def get_test_value() -> str:
        return "test:value"

    @wire
    def operation(value: str = wired(get_value)) -> str:
        return value

    assert operation() == "prod:value"

    with override_dependency(get_value, get_test_value):
        assert operation() == "test:value"

    assert operation() == "prod:value"


def test_wire_restores_existing_custom_signature() -> None:
    def operation(value: str) -> str:
        return value

    custom_signature = inspect.signature(operation)
    setattr(operation, "__signature__", custom_signature)  # noqa: B010

    wrapped = wire(operation)

    assert getattr(operation, "__signature__") is custom_signature  # noqa: B009
    assert inspect.signature(wrapped) == custom_signature
    assert wrapped("value") == "value"
