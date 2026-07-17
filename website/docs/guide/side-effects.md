# Side-effect dependencies

Some dependencies guard a call instead of feeding it a value:
authorization checks, audit trails, rate limits. Declare them with
`requires` and they resolve on every call, in declaration order, without
appearing as parameters.

Guards are not a new kind of function: they are ordinary factories whose
return value is discarded. Like every factory they stay undecorated
(`@wire` is only for entry points) and are called by Wireme, never
directly by your code.

A real guard needs context, so it declares its own wired dependencies like
any other factory. Here the current user comes from a context factory that
the application layer provides and tests override:

```python
def get_current_user() -> User:
    # In an application this reads real context: a session, a token, a
    # request. Tests swap it with override_dependency.
    return load_user_from_session()


type CurrentUserDep = Annotated[User, wired(get_current_user)]


def ensure_admin(*, user: CurrentUserDep = Wired()) -> None:
    if user.role != "admin":
        raise PermissionError(f"{user.name} is not an admin")


@wire(requires=(ensure_admin,))
def delete_account(account_id: str) -> None:
    ...
```

Generator factories clean up when the call finishes, which suits auditing
and timing:

```python
def audit(*, user: CurrentUserDep = Wired()) -> Iterator[None]:
    log(f"{user.name}: start")
    try:
        yield
    finally:
        log(f"{user.name}: end")


@wire(requires=(ensure_admin, audit))
def delete_account(account_id: str) -> None:
    ...
```

`requires` accepts any factory form and shares the per-call cache with
parameter dependencies: `ensure_admin` and `audit` see the same user, and
overriding `get_current_user` changes what every guard sees.

## Runnable example

[examples/requires.py](https://github.com/mghalix/wireme/blob/main/examples/requires.py)

Next: [Protocol dependencies](protocols.md)
