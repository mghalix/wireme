# Structure a FastAPI app

One module owns the dependency vocabulary; routers consume aliases; tests
override factories. Nothing else needs to know how anything is built.

## The dependencies module

```python title="myapp/dependencies.py"
from typing import Annotated

from wireme import Wired, wired

from myapp.database import Connection, Settings
from myapp.services import UserService

settings = Settings()  # validates the environment at import time


def get_settings() -> Settings:
    return settings


type SettingsDep = Annotated[Settings, wired(get_settings)]


def get_connection(*, config: SettingsDep = Wired()):
    connection = Connection(config.database_url)
    try:
        yield connection
    finally:
        connection.close()


type ConnectionDep = Annotated[Connection, wired(get_connection)]


def get_user_service(*, connection: ConnectionDep = Wired()) -> UserService:
    return UserService(connection=connection)


type UserServiceDep = Annotated[UserService, wired(get_user_service)]
```

## The router

Routers import aliases, not factories. `FromWeb` bridges each alias while
FastAPI keeps the request lifecycle: the connection opens on first use,
survives streaming, and closes after the response.

```python title="myapp/routers/users.py"
from fastapi import APIRouter

from wireme.fastapi import FromWeb

from myapp.dependencies import UserServiceDep

router = APIRouter()


@router.get("/users")
def list_users(service: FromWeb[UserServiceDep]) -> list[str]:
    return service.list_users()
```

## The tests

```python title="tests/test_users.py"
from wireme.fastapi import override_web_dependency

from myapp.dependencies import get_user_service


def test_users_endpoint(app, client):
    def get_test_service() -> UserService:
        return UserService(connection=FakeConnection())

    with override_web_dependency(app, get_user_service, get_test_service):
        assert client.get("/users").json() == []
```

Replacements may be sync, async, generator, or async-generator factories
with different parameter lists. Register routes before entering the
override context so all bridges are known.

!!! tip "Swap one layer, keep the rest"
    Overriding `get_connection` instead of `get_user_service` keeps the
    real service logic in play against a fake connection: choose the
    override depth per test.
