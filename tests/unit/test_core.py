from __future__ import annotations

import functools
import inspect
import typing
from collections.abc import AsyncGenerator, Generator
from typing import Annotated, Any

import pytest
from pydantic import AfterValidator, Field

from wireme import ValidationError, Wired, override_dependency, wire, wired


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


def test_keyword_only_dependency_is_injected_and_hidden() -> None:
    @wire
    def operation(value: int, *, database: Database = Wired()) -> tuple[int, str]:
        return value, database

    assert operation(1) == (1, "production")
    assert tuple(inspect.signature(operation).parameters) == ("value",)


def test_wire_requires_runs_side_effect_dependencies() -> None:
    events: list[str] = []

    def audit() -> Generator[None, None, None]:
        events.append("enter")
        try:
            yield
        finally:
            events.append("exit")

    @wire(requires=(audit,))
    def operation(value: int) -> int:
        events.append("run")
        return value

    assert operation(1) == 1
    assert events == ["enter", "run", "exit"]


def test_wire_requires_shares_the_per_call_cache() -> None:
    calls = 0

    def get_number() -> int:
        nonlocal calls
        calls += 1
        return 2

    @wire(requires=(get_number,))
    def operation(number: int = wired(get_number)) -> int:
        return number

    assert operation() == 2
    assert calls == 1


def test_wire_requires_factories_resolve_their_own_dependencies() -> None:
    def get_role() -> str:
        return "admin"

    seen_roles: list[str] = []

    def ensure_admin(*, role: str = wired(get_role)) -> None:
        seen_roles.append(role)

    @wire(requires=(ensure_admin,))
    def operation() -> str:
        return "done"

    assert operation() == "done"
    assert seen_roles == ["admin"]


def test_wire_requires_guard_sees_overridden_context() -> None:
    def get_role() -> str:
        return "admin"

    def get_viewer_role() -> str:
        return "viewer"

    def ensure_admin(*, role: str = wired(get_role)) -> None:
        if role != "admin":
            raise PermissionError("admin required")

    @wire(requires=(ensure_admin,))
    def operation() -> str:
        return "done"

    assert operation() == "done"

    with (
        override_dependency(get_role, get_viewer_role),
        pytest.raises(PermissionError, match="admin required"),
    ):
        operation()

    assert operation() == "done"


def test_configured_wire_is_a_reusable_decorator() -> None:
    project_wire = wire(cast=False, cast_result=False)

    @project_wire
    def operation(value: str = wired(get_database)) -> str:
        return value

    @project_wire
    class Service:
        def __init__(self, *, value: str = wired(get_database)) -> None:
            self.value = value

    assert operation() == "production"
    assert Service().value == "production"


def test_wire_cast_false_skips_argument_validation() -> None:
    @wire(cast=False)
    def operation(value: int) -> object:
        return value

    assert operation(typing.cast("int", "not-an-int")) == "not-an-int"


def test_wire_cast_true_validates_arguments() -> None:
    @wire
    def operation(value: int) -> int:
        return value

    with pytest.raises(ValidationError):
        operation(typing.cast("int", "not-an-int"))


def test_wire_cast_result_false_skips_return_coercion() -> None:
    @wire(cast_result=False)
    def operation() -> int:
        return typing.cast("int", "1")

    assert operation() == "1"


def test_wire_cast_result_true_coerces_return_value() -> None:
    @wire
    def operation() -> int:
        return typing.cast("int", "1")

    assert operation() == 1


def test_field_default_validates_arguments() -> None:
    @wire
    def operation(value: str = Field(..., max_length=5)) -> str:
        return value

    assert operation("ok") == "ok"

    with pytest.raises(ValidationError):
        operation("too-long")

    with pytest.raises(ValidationError):
        operation()


def test_annotated_field_constraints_validate_and_coerce() -> None:
    @wire
    def operation(count: Annotated[int, Field(gt=0, le=100)] = 20) -> int:
        return count

    assert operation() == 20
    assert operation(typing.cast("int", "7")) == 7

    with pytest.raises(ValidationError):
        operation(0)


def test_annotated_custom_validator_runs() -> None:
    def normalize(value: str) -> str:
        return value.strip().lower()

    @wire
    def operation(username: Annotated[str, AfterValidator(normalize)]) -> str:
        return username

    assert operation("  Mo ") == "mo"


def test_factory_parameters_are_validated() -> None:
    def get_limit(limit: Annotated[int, Field(gt=0, le=100)]) -> int:
        return limit

    @wire
    def operation(limit: int, *, checked: int = wired(get_limit)) -> int:
        return checked

    assert operation(50) == 50

    with pytest.raises(ValidationError):
        operation(500)


def test_class_constructor_factory_receives_caller_arguments() -> None:
    class Repository:
        def __init__(self, dsn: str) -> None:
            self.dsn = dsn

    @wire
    def operation(dsn: str, *, repository: Any = wired(Repository)) -> str:
        assert isinstance(repository, Repository)
        return repository.dsn

    assert operation("db://production") == "db://production"


def test_callable_instance_factory_receives_caller_arguments() -> None:
    class Adder:
        def __init__(self, base: int) -> None:
            self.base = base

        def __call__(self, amount: int) -> int:
            return self.base + amount

    @wire
    def operation(amount: int, *, total: int = wired(Adder(3))) -> int:
        return total

    assert operation(4) == 7


def test_staticmethod_factory() -> None:
    class Tools:
        @staticmethod
        def square(value: int) -> int:
            return value * value

    @wire
    def operation(value: int, *, squared: int = wired(Tools.square)) -> int:
        return squared

    assert operation(4) == 16


def test_bound_method_factory() -> None:
    class Prefixer:
        def __init__(self, prefix: str) -> None:
            self.prefix = prefix

        def make(self, name: str) -> str:
            return f"{self.prefix}:{name}"

    @wire
    def operation(name: str, *, tagged: str = wired(Prefixer("app").make)) -> str:
        return tagged

    assert operation("db") == "app:db"


def test_wire_on_class_wires_the_constructor() -> None:
    @wire
    class Service:
        def __init__(self, *, database: Database = Wired()) -> None:
            self.database = database

    service = Service()

    assert service.database == "production"
    assert tuple(inspect.signature(Service).parameters) == ()


def test_wire_on_class_accepts_configuration() -> None:
    events: list[str] = []

    def audit() -> None:
        events.append("audit")

    @wire(requires=(audit,))
    class Service:
        def __init__(self, *, database: Database = Wired()) -> None:
            self.database = database

    assert Service().database == "production"
    assert events == ["audit"]


def test_wire_on_class_without_own_init_is_rejected() -> None:
    class Service:
        pass

    with pytest.raises(TypeError, match="requires the class to define __init__"):
        wire(Service)


def test_callable_object_dependency() -> None:
    class ValueFactory:
        def __call__(self) -> str:
            return "callable"

    factory = ValueFactory()

    @wire
    def operation(value: str = wired(factory)) -> str:
        return value

    assert operation() == "callable"


def test_functools_partial_dependency() -> None:
    def get_value(prefix: str) -> str:
        return f"{prefix}:value"

    factory = functools.partial(get_value, "partial")

    @wire
    def operation(value: str = wired(factory)) -> str:
        return value

    assert operation() == "partial:value"


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


def testwire_restores_existing_custom_signature() -> None:
    def operation(value: str) -> str:
        return value

    custom_signature = inspect.signature(operation)
    setattr(operation, "__signature__", custom_signature)  # noqa: B010

    wrapped = wire(operation)

    assert getattr(operation, "__signature__") is custom_signature  # noqa: B009
    assert inspect.signature(wrapped) == custom_signature
    assert wrapped("value") == "value"
