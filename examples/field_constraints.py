"""Parameter validation with pydantic constraints, without models.

@wire validates every annotated parameter through pydantic, so a single
constrained parameter needs neither a BaseModel nor a TypeAdapter: the
constraint lives in the signature via Annotated. Factory parameters are
validated the same way.
"""

from __future__ import annotations

import typing
from typing import Annotated

from pydantic import AfterValidator, Field

from wireme import ValidationError, wire, wired

type Limit = Annotated[int, Field(gt=0, le=100)]
type Username = Annotated[str, Field(min_length=2, max_length=32)]


def normalize(value: str) -> str:
    return value.strip().lower()


type NormalizedUsername = Annotated[Username, AfterValidator(normalize)]


@wire
def search_users(query: Username, limit: Limit = 20) -> str:
    return f"searching {query!r}, limit {limit}"


def get_page_size(page_size: Limit = 20) -> int:
    return page_size


@wire
def list_users(page_size: int, *, size: int = wired(get_page_size)) -> int:
    return size


@wire
def register(username: NormalizedUsername) -> str:
    return username


if __name__ == "__main__":
    assert search_users("mo") == "searching 'mo', limit 20"

    # Untyped boundary input (a CLI flag, a queue payload) is coerced.
    assert search_users("mo", typing.cast("int", "50")).endswith("limit 50")

    for invalid in (lambda: search_users("m"), lambda: search_users("mo", 0)):
        try:
            invalid()
        except ValidationError:
            pass
        else:
            raise AssertionError("expected the constraint to reject the input")

    assert list_users(50) == 50

    try:
        list_users(500)
    except ValidationError:
        print("factory parameters are constrained too")

    assert register("  Mo ") == "mo"
    print("constraints and custom validators, no BaseModel required")
