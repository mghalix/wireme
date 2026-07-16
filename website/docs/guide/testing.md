# Testing

## Overrides

`override_dependency()` temporarily replaces a factory everywhere it is
used, including nested dependencies:

```python
from wireme import override_dependency


def get_test_database() -> Database:
    return TestDatabase()


with override_dependency(get_database, get_test_database):
    create_user("mo")
```

Overrides are restored when the context exits, including after exceptions.
Nested overrides restore the previous outer override correctly.

The provider is shared at process level. Use overrides for isolated tests
and application setup, not concurrent request-level mutation.

## Explicit values take precedence

A caller may still provide a dependency explicitly by keyword; the passed
value wins over injection:

```python
class TestDatabase(Database):
    pass


create_user("mo", database=TestDatabase())
```

Only the keyword form reaches an injected parameter. A positional value is
not mapped to it, which is another reason to declare injected parameters
after `*`: type checkers then reject the positional call outright.

This is useful for one-off composition. For test suites, prefer
`override_dependency()` so every nested dependency sees the replacement.

## Runnable example

[examples/overrides.py](https://github.com/mghalix/wireme/blob/main/examples/overrides.py)

Next: [Side-effect dependencies](side-effects.md)
