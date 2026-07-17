from __future__ import annotations

import functools
import inspect
import typing
from collections.abc import AsyncGenerator, Generator
from typing import Annotated, Any

import pytest
from fast_depends import Depends
from fast_depends.library import CustomField

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


def test_wire_parentheses_returns_a_reusable_decorator() -> None:
    project_wire = wire()

    @project_wire
    def operation(value: str = wired(get_database)) -> str:
        return value

    @project_wire
    class Service:
        def __init__(self, *, value: str = wired(get_database)) -> None:
            self.value = value

    assert operation() == "production"
    assert Service().value == "production"


def test_wire_preserves_argument_values() -> None:
    @wire
    def operation(value: int) -> object:
        return value

    assert operation(typing.cast("int", "not-an-int")) == "not-an-int"


def test_wire_preserves_return_values() -> None:
    @wire
    def operation() -> int:
        return typing.cast("int", "1")

    assert operation() == "1"


def test_wired_preserves_factory_results() -> None:
    def get_number() -> int:
        return typing.cast("int", "1")

    @wire
    def operation(*, number: int = wired(get_number)) -> object:
        return number

    assert operation() == "1"


def test_nested_factories_preserve_shared_arguments() -> None:
    def get_number(number: int) -> int:
        return number

    @wire
    def operation(number: int, *, injected: int = wired(get_number)) -> object:
        return injected

    assert operation(typing.cast("int", "7")) == "7"


def test_wired_disables_upstream_casting() -> None:
    marker = typing.cast("Any", wired(get_database))

    assert marker.cast is False
    assert marker.cast_result is False


def test_wire_rejects_fast_depends_custom_field_default() -> None:
    source = typing.cast("str", CustomField())

    def operation(value: str = source) -> str:
        return value

    with pytest.raises(TypeError, match="does not support FastDepends CustomField"):
        wire(operation)


def test_wired_rejects_fast_depends_annotated_custom_field() -> None:
    source = CustomField()

    def get_value(value: Annotated[str, source]) -> str:
        return value

    with pytest.raises(TypeError, match="does not support FastDepends CustomField"):
        wired(get_value)


def test_wire_rejects_custom_field_nested_behind_upstream_depends() -> None:
    source = typing.cast("str", CustomField())

    def get_value(value: str = source) -> str:
        return value

    dependency = typing.cast("str", Depends(get_value))

    def operation(*, value: str = dependency) -> str:
        return value

    with pytest.raises(TypeError, match="does not support FastDepends CustomField"):
        wire(operation)


def test_override_rejects_fast_depends_custom_field() -> None:
    source = typing.cast("str", CustomField())

    def replacement(value: str = source) -> str:
        return value

    with (
        pytest.raises(TypeError, match="does not support FastDepends CustomField"),
        override_dependency(get_database, replacement),
    ):
        pass


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


def test_override_dependency_preserves_replacement_result() -> None:
    def get_number() -> int:
        return 1

    def get_uncoerced_number() -> int:
        return typing.cast("int", "1")

    @wire
    def operation(*, number: int = wired(get_number)) -> object:
        return number

    with override_dependency(get_number, get_uncoerced_number):
        assert operation() == "1"


def test_override_dependency_can_precede_dependency_registration() -> None:
    def get_number() -> int:
        return 1

    def get_test_number() -> int:
        return 2

    with override_dependency(get_number, get_test_number):

        @wire
        def operation(*, number: int = wired(get_number)) -> int:
            return number

        assert operation() == 2

    assert operation() == 1


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
