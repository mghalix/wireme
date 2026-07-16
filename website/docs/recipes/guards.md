# Guard calls with requires

Authorization checks, audit trails, and rate limits observe or block a call
without feeding it a value. Declare them with `requires`; they run in
declaration order before the call, and generator guards clean up after it.

A real guard needs context, so it declares its own wired dependencies. The
current user comes from a context factory the application layer provides:

```python title="myapp/guards.py"
from collections.abc import Iterator
from typing import Annotated

from wireme import Wired, wired

from myapp.auth import User, load_user_from_session


def get_current_user() -> User:
    return load_user_from_session()


type CurrentUserDep = Annotated[User, wired(get_current_user)]


def ensure_admin(*, user: CurrentUserDep = Wired()) -> None:
    if user.role != "admin":
        raise PermissionError(f"{user.name} is not an admin")


def audit(*, user: CurrentUserDep = Wired()) -> Iterator[None]:
    log(f"{user.name}: start")
    try:
        yield
    finally:
        log(f"{user.name}: end")
```

```python title="myapp/accounts.py"
from wireme import wire

from myapp.guards import audit, ensure_admin


@wire(requires=(ensure_admin, audit))
def delete_account(account_id: str) -> None:
    ...
```

Three properties make this production-grade:

- **Shared context, resolved once.** `ensure_admin` and `audit` see the
  same user per call through the per-call cache.
- **Testable.** `override_dependency(get_current_user, get_viewer)` makes
  every guard see the swapped user; no monkeypatching.
- **Composable.** Guards are ordinary factories: they nest, cache, and
  override like any other dependency, and `requires` simply discards their
  return value.

!!! note "Guards stay undecorated"
    `@wire` marks entry points. Guards are recipes the engine calls, so a
    direct `audit()` call would receive the `Wired()` placeholder instead
    of a real user. If several functions share the same guard set, bind it
    once: `admin_wire = wire(requires=(ensure_admin, audit))`.
