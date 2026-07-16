"""Side-effect dependencies with wire(requires=...).

Guards observe or block a call without feeding it a value. A real guard
needs context, so it declares its own wired dependencies: here the current
user comes from a context factory that the application layer provides and
tests override. Guards run in declaration order before the call.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Annotated

from wireme import Wired, override_dependency, wire, wired

audit_log: list[str] = []


@dataclass
class User:
    name: str
    role: str


def get_current_user() -> User:
    # In an application this reads real context: a session, a token, a
    # request. Tests and other environments swap it with override_dependency.
    return User(name="mo", role="admin")


type CurrentUserDep = Annotated[User, wired(get_current_user)]


# Guards are ordinary factories: Wireme calls them, never your code. They
# stay undecorated like every factory (get_current_user included), because
# @wire marks entry points while wired() and requires consume recipes. A
# direct call such as audit() would receive the Wired() placeholder instead
# of a real user, exactly as calling get_current_user's dependents directly
# would.
def ensure_admin(*, user: CurrentUserDep = Wired()) -> None:
    if user.role != "admin":
        raise PermissionError(f"{user.name} is not an admin")


def audit(*, user: CurrentUserDep = Wired()) -> Iterator[None]:
    audit_log.append(f"{user.name}: start")
    try:
        yield
    finally:
        audit_log.append(f"{user.name}: end")


@wire(requires=(ensure_admin, audit))
def delete_account(account_id: str) -> str:
    audit_log.append(f"delete {account_id}")
    return account_id


if __name__ == "__main__":
    assert delete_account("legacy-account") == "legacy-account"
    # Both guards saw the same user: the per-call cache resolved it once.
    assert audit_log == ["mo: start", "delete legacy-account", "mo: end"]

    def get_viewer() -> User:
        return User(name="sam", role="viewer")

    with override_dependency(get_current_user, get_viewer):
        try:
            delete_account("legacy-account")
        except PermissionError as error:
            print(f"guard blocked the call: {error}")
        else:
            raise AssertionError("expected the guard to block the call")

    print("guards read injected context; overrides swap it in tests")
