# Building integrations

Wireme can be the small DI primitive behind a project-specific API. For
example, a service or plugin registry can expose `wired_service(ServiceType)`
while still using Wireme for resolution, typing, caching, and overrides.

```python
import functools

from collections.abc import Callable
from typing import cast

from wireme import WiremeError, wired


class ServiceUnavailableError(WiremeError):
    pass


_services: dict[type[object], object] = {}


@functools.cache
def require_service[T](service_type: type[T]) -> Callable[[], T]:
    def dependency() -> T:
        try:
            service = _services[service_type]
        except KeyError as error:
            raise ServiceUnavailableError(
                f"{service_type.__name__} is not registered."
            ) from error

        return cast(T, service)

    return dependency


def wired_service[T](service_type: type[T]) -> T:
    return wired(require_service(service_type))
```

Caching the generated factory gives it stable identity, which is important
when using `override_dependency()`.

## Wire many methods at once

`wire` deliberately has no method scanning: on a class it wires only the
constructor, and member selection (include and exclude rules) is a concern
of its own. When a class has many wired methods, compose `wire` with a
small generic combinator that owns the selection:

```python
@apply(wire, include=("load", "reload"))
class Loader:
    def load(self, *, database: DatabaseDep = Wired()) -> str: ...
    def reload(self, *, database: DatabaseDep = Wired()) -> str: ...
```

`apply` is ten lines of user code, works with any decorator (tracing and
timing too, not just `wire`), and keeps the selection rules in one place in
your project instead of inside every tool.

## Runnable examples

[examples/custom_integration.py](https://github.com/mghalix/wireme/blob/main/examples/custom_integration.py),
[examples/method_wiring.py](https://github.com/mghalix/wireme/blob/main/examples/method_wiring.py)
