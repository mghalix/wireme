"""Wire several methods at once by composing wire with an apply combinator.

wire deliberately has no method scanning: on a class it wires only the
constructor. When a class has many wired methods, keep the selection logic
in a small generic combinator that applies any decorator to named methods.
Copy this pattern; it works with wire, but also with tracing, timing, or
any other per-function decorator.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Annotated, Any, Protocol

from wireme import Wired, wire, wired


class ClassDecorator(Protocol):
    """Decorate a class in place while preserving its type."""

    def __call__[T](self, cls: type[T], /) -> type[T]: ...


def apply(
    decorator: Callable[[Callable[..., Any]], Callable[..., Any]],
    /,
    *,
    include: Sequence[str],
) -> ClassDecorator:
    """Apply a decorator to the named methods a class defines itself."""

    def decorate[T](cls: type[T], /) -> type[T]:
        for name in include:
            setattr(cls, name, decorator(vars(cls)[name]))
        return cls

    return decorate


class Database:
    def read(self) -> str:
        return "data"


def get_database() -> Database:
    return Database()


type DatabaseDep = Annotated[Database, wired(get_database)]


@apply(wire, include=("load", "reload"))
class Loader:
    def load(self, *, database: DatabaseDep = Wired()) -> str:
        return database.read()

    def reload(self, *, database: DatabaseDep = Wired()) -> str:
        return database.read().upper()


if __name__ == "__main__":
    loader = Loader()

    assert loader.load() == "data"
    assert loader.reload() == "DATA"

    print("apply composes wire onto selected methods")
