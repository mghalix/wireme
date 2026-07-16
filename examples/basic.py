from __future__ import annotations

from typing import Annotated

from wireme import Wired, wire, wired


class Database:
    def write(self, data: str) -> None:
        print(f"writing data: {data}")


def get_database() -> Database:
    return Database()


@wire
def process_text(
    text: str,
    *,
    database: Database = wired(get_database),
) -> None:
    print("Processing with a direct dependency...")
    database.write(text)


type DatabaseDep = Annotated[Database, wired(get_database)]


@wire
def process_text_reusable(
    text: str,
    *,
    database: DatabaseDep = Wired(),
) -> None:
    print("Processing with a reusable dependency...")
    database.write(text)


if __name__ == "__main__":
    process_text("Hello, world")
    process_text_reusable("Hello again")
