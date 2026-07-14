from __future__ import annotations

from typing import Annotated, Protocol, runtime_checkable

from wireme import Wired, wire, wired


@runtime_checkable
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
    database: DatabaseDep = Wired(),
) -> None:
    database.write(text)


if __name__ == "__main__":
    process_text("injected")

    # An explicit argument takes precedence over dependency injection.
    process_text("explicit", DebugDatabase())
