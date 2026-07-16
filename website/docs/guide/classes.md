# Wiring classes

Use constructor injection when the dependency belongs to the object's state.
Decorate the class; it wires the constructor:

```python
from typing import Annotated

from wireme import Wired, wire, wired


type DatabaseDep = Annotated[Database, wired(get_database)]


@wire
class TextProcessor:
    def __init__(self, *, database: DatabaseDep = Wired()) -> None:
        self._database = database

    def process(self, text: str) -> None:
        self._database.write(text)


TextProcessor().process("Hello from constructor injection")
```

The class decorator wires only the `__init__` the class defines, and is
equivalent to applying `@wire` to `__init__` directly. It never scans or
wraps other methods, so injection stays visible where it happens. A class
without its own `__init__` is rejected with a `TypeError`.

Use method injection when only a specific operation needs the dependency:

```python
class TextProcessor:
    @wire
    def process(
        self,
        text: str,
        *,
        database: DatabaseDep = Wired(),
    ) -> None:
        database.write(text)


TextProcessor().process("Hello from method injection")
```

Constructor injection is useful for dependencies shared across multiple
methods. Method injection keeps the object stateless when only one operation
needs the dependency.

## Runnable example

[examples/classes.py](https://github.com/mghalix/wireme/blob/main/examples/classes.py)

Next: [The dependency graph](dependency-graph.md)
