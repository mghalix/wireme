from __future__ import annotations

from typing import Annotated

from wireme import Wired, override_dependency, wire, wired


def get_value() -> str:
    return "production"


def get_test_value() -> str:
    return "test"


type ValueDep = Annotated[str, wired(get_value)]


@wire
def operation(value: ValueDep = Wired()) -> str:
    return value


assert operation() == "production"

with override_dependency(get_value, get_test_value):
    assert operation() == "test"

assert operation() == "production"

print("wireme smoke test passed")
