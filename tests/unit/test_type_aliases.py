from __future__ import annotations

import inspect
from typing import Annotated

from wireme import Wired, wire, wired


def get_database() -> str:
    return "production"


type DatabaseDep = Annotated[str, wired(get_database)]


def get_connection_string(*, database: DatabaseDep = Wired()) -> str:
    return f"db://{database}"


type ConnectionStringDep = Annotated[str, wired(get_connection_string)]


def ensure_ready(*, database: DatabaseDep = Wired()) -> None:
    assert database == "production"


class SlottedFactory:
    __slots__ = ()

    def __call__(self) -> str:
        return "slotted"


def test_pep_695_alias_with_postponed_annotations() -> None:

    @wire
    def operation(database: DatabaseDep = Wired()) -> str:
        return database

    assert operation() == "production"
    assert tuple(inspect.signature(operation).parameters) == ()


def test_nested_factory_resolves_its_own_alias_dependency() -> None:

    @wire
    def operation(*, connection: ConnectionStringDep = Wired()) -> str:
        return connection

    assert operation() == "db://production"


def test_requires_factory_resolves_its_own_alias_dependency() -> None:

    @wire(requires=(ensure_ready,))
    def operation() -> str:
        return "done"

    assert operation() == "done"


def test_factory_rejecting_signature_assignment_still_works() -> None:
    factory = SlottedFactory()

    @wire
    def operation(value: str = wired(factory)) -> str:
        return value

    assert operation() == "slotted"
