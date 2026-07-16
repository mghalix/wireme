"""Control pydantic validation per function with cast and cast_result.

Validation is on by default: arguments and return values are coerced and
checked. Turn it off for hot paths that trust their inputs.
"""

from __future__ import annotations

import typing

from wireme import ValidationError, wire


@wire
def validated(value: int) -> int:
    return value


@wire(cast=False, cast_result=False)
def unvalidated(value: int) -> int:
    return value


if __name__ == "__main__":
    # typing.cast models untrusted input reaching a typed boundary.
    untrusted: object = "7"

    assert validated(typing.cast("int", untrusted)) == 7

    try:
        validated(typing.cast("int", "not-a-number"))
    except ValidationError:
        print("invalid input rejected")
    else:
        raise AssertionError("expected validation to reject the input")

    assert unvalidated(typing.cast("int", untrusted)) == "7"
    print("validation on by default, off for hot paths")
