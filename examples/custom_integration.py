from __future__ import annotations

import functools
from collections.abc import Callable
from typing import Protocol, cast, runtime_checkable

from wireme import WiremeError, wire, wired


class ServiceUnavailableError(WiremeError):
    pass


_services: dict[type[object], object] = {}


def register_service[T](service_type: type[T], implementation: T) -> None:
    _services[service_type] = implementation


@functools.cache
def require_service[T](service_type: type[T]) -> Callable[[], T]:
    """Create a stable dependency factory for a registered service type."""

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
    """Declare a registered service as a typed Wireme dependency."""
    return wired(require_service(service_type))


@runtime_checkable
class Storage(Protocol):
    def write(self, path: str, data: bytes) -> None: ...


class LocalStorage:
    def write(self, path: str, data: bytes) -> None:
        print(f"stored {len(data)} bytes at {path}")


@wire
def save_document(
    path: str,
    data: bytes,
    storage: Storage = wired_service(Storage),  # noqa: B008
) -> None:
    storage.write(path, data)


if __name__ == "__main__":
    register_service(Storage, LocalStorage())
    save_document("report.txt", b"wireme")
