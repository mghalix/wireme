"""Provide nested-safe FastAPI dependency overrides."""

from __future__ import annotations

import contextlib
import typing
from collections.abc import AsyncIterator, Awaitable, Callable, Generator, Iterator

from wireme.fastapi._dependencies import get_override_pairs

from ._compat import FastAPI

type _WebFactory[T] = (
    Callable[..., Awaitable[T]]
    | Callable[..., AsyncIterator[T]]
    | Callable[..., Iterator[T]]
    | Callable[..., T]
)

type _AnyFactory = Callable[..., typing.Any]


_MISSING = object()


@contextlib.contextmanager
def override_web_dependency[T](
    app: FastAPI,
    original: _WebFactory[T],
    replacement: _WebFactory[T],
    /,
) -> Generator[None, None, None]:
    """Temporarily replace a FastAPI dependency.

    Both direct FastAPI dependencies and adapters created by
    FromWeb[WiredAlias] are overridden. Nested contexts restore the previous
    replacement correctly, including after exceptions. Replacements may be
    sync, async, generator, or async-generator factories with different
    parameter lists.

    Bridged adapters are discovered when the context is entered, so routes
    using FromWeb must be registered before entering the override context.
    A FromWeb annotation evaluated for the first time inside the context is
    not overridden until the context is entered again.
    """
    pairs = get_override_pairs(
        typing.cast("_AnyFactory", original),
        typing.cast("_AnyFactory", replacement),
    )

    previous: dict[_AnyFactory, object] = {}

    for dependency, override in pairs:
        previous[dependency] = app.dependency_overrides.get(
            dependency,
            _MISSING,
        )
        app.dependency_overrides[dependency] = override

    try:
        yield
    finally:
        for dependency, _ in reversed(pairs):
            existing = previous[dependency]

            if existing is _MISSING:
                app.dependency_overrides.pop(dependency, None)
            else:
                app.dependency_overrides[dependency] = typing.cast(
                    "_AnyFactory",
                    existing,
                )
