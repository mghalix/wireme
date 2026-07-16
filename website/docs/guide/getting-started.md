# Getting started

## Installation

```bash
uv add wireme
```

With the optional FastAPI integration:

```bash
uv add 'wireme[fastapi]'
```

Wireme requires Python 3.12 or newer.

## Wire a function

```python
from wireme import wire, wired


class Database:
    def write(self, value: str) -> None:
        print(f"writing: {value}")


def get_database() -> Database:
    return Database()


@wire
def process_text(
    text: str,
    *,
    database: Database = wired(get_database),
) -> None:
    database.write(text)


process_text("Hello, world")
```

Callers only provide application inputs. Wireme resolves `database`
automatically.

Declare injected parameters keyword-only, after `*`. They are never passed
by position, the `*` groups them visibly at the end of the signature, and
type checkers reject accidental positional values.

Injected parameters are also removed from the public runtime signature:

```python
import inspect

assert str(inspect.signature(process_text)) == "(text: str) -> None"
```

## Reusable dependencies

Use `Annotated` when the same dependency appears in multiple callables:

```python
from typing import Annotated

from wireme import Wired, wire, wired


type DatabaseDep = Annotated[Database, wired(get_database)]


@wire
def create_user(
    username: str,
    *,
    database: DatabaseDep = Wired(),
) -> None:
    database.write(username)


create_user("mo")
```

`wired(get_database)` stores the dependency declaration in the annotation.
`Wired()` tells type checkers and call sites that the argument does not need
to be passed explicitly.

Note the division of roles, because it holds everywhere in Wireme: `@wire`
marks entry points, the functions your code calls. Factories like
`get_database` stay undecorated: they are recipes that Wireme calls while
resolving an entry point. Once a factory declares `Wired()` parameters of
its own, calling it directly would hand it the `Wired()` placeholder
instead of a resolved value, so factories are only ever invoked through
the dependency graph.

## Ruff configuration

Ruff's `B008` rule normally rejects function calls in defaults. Tell Ruff
that `Wired()` is an immutable marker:

```toml
[tool.ruff.lint.flake8-bugbear]
extend-immutable-calls = ["wireme.Wired"]
```

Declarations using `wired(factory)` may also need your project's normal DI
rule configuration, depending on which Ruff rules are enabled.

## Runnable example

[examples/basic.py](https://github.com/mghalix/wireme/blob/main/examples/basic.py)

Next: [Wiring classes](classes.md)
