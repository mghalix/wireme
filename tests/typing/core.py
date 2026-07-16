from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from typing import Annotated, assert_type

from wireme import Wired, override_dependency, wire, wired


def sync_dependency() -> str:
    return "sync"


async def async_dependency() -> str:
    return "async"


def generator_dependency() -> Iterator[str]:
    yield "generator"


async def async_generator_dependency() -> AsyncIterator[str]:
    yield "async-generator"


assert_type(wired(sync_dependency), str)
assert_type(wired(async_dependency), str)
assert_type(wired(generator_dependency), str)
assert_type(wired(async_generator_dependency), str)

Value = Annotated[str, wired(sync_dependency)]


@wire
def direct(value: str = wired(sync_dependency)) -> str:
    return value


@wire
def annotated(value: Value = Wired()) -> str:
    return value


assert_type(direct(), str)
assert_type(annotated(), str)


def guard() -> None:
    return None


@wire(cast=False, cast_result=False)
def uncast(value: str = wired(sync_dependency)) -> str:
    return value


@wire(requires=(guard,))
def guarded(value: str = wired(sync_dependency)) -> str:
    return value


assert_type(uncast(), str)
assert_type(guarded(), str)


@wire
class WiredService:
    def __init__(self, *, value: str = wired(sync_dependency)) -> None:
        self.value = value


assert_type(WiredService(), WiredService)

with override_dependency(async_dependency, sync_dependency):
    pass


def original_dependency(value: int) -> str:
    return str(value)


def replacement_dependency() -> str:
    return "replacement"


with override_dependency(original_dependency, replacement_dependency):
    pass
