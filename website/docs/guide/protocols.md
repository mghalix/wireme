# Protocol dependencies

A protocol can describe the dependency interface. When runtime validation is
active, make the protocol runtime-checkable:

```python
from typing import Annotated, Protocol, runtime_checkable

from wireme import Wired, wire, wired


@runtime_checkable
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
