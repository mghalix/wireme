from __future__ import annotations

from typing import Annotated

from wireme import Wired, override_dependency, wire, wired


class Database:
    def __init__(self, name: str) -> None:
        self.name = name


def get_database() -> Database:
    return Database("production")


def get_test_database() -> Database:
    return Database("test")


type DatabaseDep = Annotated[Database, wired(get_database)]


@wire
def database_name(*, database: DatabaseDep = Wired()) -> str:
    return database.name


if __name__ == "__main__":
    assert database_name() == "production"

    with override_dependency(get_database, get_test_database):
        assert database_name() == "test"

    assert database_name() == "production"
    print("override restored successfully")
