"""Every callable form works as a factory.

A factory is anything callable: a function, a class (the constructor runs
and the instance is injected), a pre-built callable instance, a
staticmethod, or a bound method. Factories may also consume the caller's
arguments by name, so one incoming value can feed both the entry point and
its dependencies.
"""

from __future__ import annotations

from typing import Annotated

from wireme import Wired, wire, wired


class Repository:
    def __init__(self, dsn: str) -> None:
        self.dsn = dsn


type RepositoryDep = Annotated[Repository, wired(Repository)]


@wire
def migrate(dsn: str, *, repository: RepositoryDep = Wired()) -> str:
    return f"migrating {repository.dsn}"


class Sampler:
    def __init__(self, rate: int) -> None:
        self.rate = rate

    def __call__(self) -> int:
        return self.rate


@wire
def sample(*, rate: int = wired(Sampler(10))) -> int:
    return rate


class Clock:
    @staticmethod
    def timezone() -> str:
        return "UTC"

    def __init__(self, offset: int) -> None:
        self.offset = offset

    def hour(self, base: int) -> int:
        return base + self.offset


@wire
def timestamp(base: int, *, zone: str = wired(Clock.timezone)) -> str:
    return f"{base}:00 {zone}"


@wire
def local_hour(base: int, *, hour: int = wired(Clock(3).hour)) -> int:
    return hour


if __name__ == "__main__":
    assert migrate("db://production") == "migrating db://production"
    assert sample() == 10
    assert timestamp(9) == "9:00 UTC"
    assert local_hour(9) == 12

    print("classes, instances, static and bound methods all inject")
