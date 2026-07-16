from __future__ import annotations

from typing import Annotated

from wireme import Wired, wire, wired


class Database:
    def write(self, data: str) -> None:
        print(f"Writing {data!r} to the database")


def get_database() -> Database:
    return Database()


type DatabaseDep = Annotated[Database, wired(get_database)]


@wire
class StatefulTextProcessor:
    """Use constructor injection when the dependency is part of object state."""

    def __init__(self, *, database: DatabaseDep = Wired()) -> None:
        self._database = database

    def process(self, text: str) -> None:
        print("Processing with constructor injection...")
        self._database.write(text)


class StatelessTextProcessor:
    """Use method injection when only one operation needs the dependency."""

    @wire
    def process(
        self,
        text: str,
        *,
        database: DatabaseDep = Wired(),
    ) -> None:
        print("Processing with method injection...")
        database.write(text)


StatefulTextProcessor().process("Hello from the constructor")
StatelessTextProcessor().process("Hello from the method")
