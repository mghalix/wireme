from __future__ import annotations

import inspect
from typing import Annotated

from wireme import Wired, wire, wired


def get_database() -> str:
    return "production"


type DatabaseDep = Annotated[str, wired(get_database)]


def test_pep_695_alias_with_postponed_annotations() -> None:

    @wire
    def operation(database: DatabaseDep = Wired()) -> str:
        return database

    assert operation() == "production"
    assert tuple(inspect.signature(operation).parameters) == ()
