# Protocol dependencies

A protocol can describe the dependency interface without imposing a concrete
implementation:

```python
from typing import Annotated, Protocol

from wireme import Wired, wire, wired


class DatabaseLike(Protocol):
    def write(self, value: str) -> None: ...


type DatabaseDep = Annotated[DatabaseLike, wired(get_database)]


@wire
def process(
    value: str,
    *,
    database: DatabaseDep = Wired(),
) -> None:
    database.write(value)
```

## Runnable example

[examples/protocols.py](https://github.com/mghalix/wireme/blob/main/examples/protocols.py)

Next: [FastAPI integration](fastapi.md)
