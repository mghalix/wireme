from __future__ import annotations

from typing import Annotated, Protocol

from wireme import Wired, wire, wired


class DatabaseLike(Protocol):
    def write(self, data: str) -> None: ...


class Database:
    def write(self, data: str) -> None:
        print(f"database: {data}")


class DebugDatabase:
    def write(self, data: str) -> None:
        print(f"debug database: {data}")


def get_database() -> Database:
    return Database()


type DatabaseDep = Annotated[DatabaseLike, wired(get_database)]


@wire
def process_text(
    text: str,
    *,
    database: DatabaseDep = Wired(),
) -> None:
    database.write(text)


if __name__ == "__main__":
    process_text("injected")

    # An explicit keyword argument takes precedence over dependency
    # injection. It is a deliberate feature for one-off composition; use
    # override_dependency() when every nested dependency must see the
    # replacement. Injected parameters are declared after *, so a positional
    # value is a type error instead of a silently ignored argument.
    process_text("explicit", database=DebugDatabase())
