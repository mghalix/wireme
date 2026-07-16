from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from wireme import Wired, wire, wired


class Database:
    def __init__(self, name: str) -> None:
        self.name = name


def get_database() -> Database:
    return Database("production")


type DatabaseDep = Annotated[
    Database,
    wired(get_database),
]


class WiredService:
    @wire
    def __init__(
        self,
        database: DatabaseDep = Wired(),
    ) -> None:
        self.database = database


@wire
class ClassWiredService:
    def __init__(
        self,
        *,
        database: DatabaseDep = Wired(),
    ) -> None:
        self.database = database


class PlainService:
    def __init__(self) -> None:
        self.name = "plain"


class UserService:
    def __init__(self, database: Database) -> None:
        self.database = database


def get_user_service(
    database: DatabaseDep = Wired(),
) -> UserService:
    return UserService(database)


type UserServiceDep = Annotated[
    UserService,
    wired(get_user_service),
]


async def get_async_user_service(
    database: DatabaseDep = Wired(),
) -> UserService:
    return UserService(database)


type AsyncUserServiceDep = Annotated[
    UserService,
    wired(get_async_user_service),
]


def get_test_user_service() -> UserService:
    return UserService(Database("test"))


def get_outer_user_service() -> UserService:
    return UserService(Database("outer"))


def get_inner_user_service() -> UserService:
    return UserService(Database("inner"))


def get_direct_value(prefix: str = "production") -> str:
    return f"{prefix}:value"


def get_test_direct_value() -> str:
    return "test:value"


type DirectValueDep = Annotated[
    str,
    Depends(get_direct_value),
]
