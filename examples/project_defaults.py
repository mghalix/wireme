"""Project-wide wire defaults through a bound decorator.

The configured form of wire returns a reusable decorator. Bind your
preferred options once in a project module (for example myapp/di.py) and
import that binding everywhere. There is no process-global configuration:
a bound decorator is explicit, import-order safe, and cannot change the
behavior of libraries that use Wireme themselves.
"""

from __future__ import annotations

import typing

import wireme
from wireme import wired

# myapp/di.py would contain exactly this line; the rest of the project
# imports wire from there instead of from wireme.
wire = wireme.wire(cast=False, cast_result=False)


def get_multiplier() -> int:
    return 3


@wire
def scale(value: int, *, multiplier: int = wired(get_multiplier)) -> int:
    return value * multiplier


@wire
class Scaler:
    def __init__(self, *, multiplier: int = wired(get_multiplier)) -> None:
        self.multiplier = multiplier


if __name__ == "__main__":
    assert scale(2) == 6
    assert Scaler().multiplier == 3

    # cast=False means arguments pass through unvalidated: a stray string
    # is repeated, not coerced. Choose defaults deliberately.
    assert scale(typing.cast("int", "2")) == "222"

    print("one binding in myapp/di.py configures the whole project")
