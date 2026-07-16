# Test with overrides

`override_dependency` replaces a factory everywhere it is used, including
nested dependencies, and restores the previous state on exit, even after
exceptions. Nested contexts restore the outer override correctly.

## A pytest fixture per swap

Wrap common swaps in fixtures so tests declare intent, not mechanics:

```python title="tests/conftest.py"
from collections.abc import Iterator

import pytest

from wireme import override_dependency

from myapp.dependencies import get_connection
from tests.fakes import FakeConnection


def get_fake_connection() -> Iterator[FakeConnection]:
    connection = FakeConnection()
    try:
        yield connection
    finally:
        connection.assert_all_released()


@pytest.fixture
def fake_connection() -> Iterator[None]:
    with override_dependency(get_connection, get_fake_connection):
        yield
```

```python title="tests/test_reports.py"
def test_report_uses_the_fake(fake_connection: None) -> None:
    assert make_report() == "report against fake"
```

Replacement factories may have different parameter lists and any form:
sync, async, generator, or async-generator. A generator replacement keeps
its cleanup semantics, so the fake above can verify its own teardown.

## Layered overrides

Overrides nest, so a test can specialize what a fixture set up:

```python
def test_slow_database(fake_connection: None) -> None:
    with override_dependency(get_connection, get_slow_connection):
        assert make_report() == "report against slow"
    # the fixture's fake is active again here
```

## One-off values beat context managers sometimes

For a single call, pass the dependency explicitly by keyword instead of
overriding:

```python
make_report(config=Settings(database_url="sqlite://:memory:"))
```

!!! warning "Process-level provider"
    Overrides mutate a provider shared across the process. Use them for
    isolated tests and application setup, not concurrent request-level
    mutation; parallel test processes (pytest-xdist) each get their own.
