"""Provide FastAPI dependency annotations backed by Wireme."""

from __future__ import annotations

import functools
import typing
from collections.abc import AsyncIterator, Callable
from contextlib import AsyncExitStack
from typing import TYPE_CHECKING, Annotated, Any

from wireme._core import _CallModel, _Dependant
from wireme._impl import _factory_model, _HasSignature

from ._compat import Depends

type _Factory = Callable[..., Any]


_bridges: dict[
    _Factory,
    dict[bool, _Factory],
] = {}


def _unwrap_type_alias(value: object, /) -> object:
    """Recursively unwrap PEP 695 runtime aliases."""
    while isinstance(value, typing.TypeAliasType):
        value = value.__value__

    return value


def _resolve_from_web_argument(
    dependency: object,
    /,
) -> tuple[object, _Dependant | None]:
    """Resolve a plain annotation or one Wireme dependency alias."""
    dependency = _unwrap_type_alias(dependency)

    if typing.get_origin(dependency) is not typing.Annotated:
        return dependency, None

    arguments = typing.get_args(dependency)
    annotation = _unwrap_type_alias(arguments[0])
    metadata = arguments[1:]

    markers = tuple(item for item in metadata if isinstance(item, _Dependant))

    if not markers:
        message = (
            "FromWeb[...] received an Annotated alias that does not contain "
            "wired(...). Pass a concrete type or a Wireme dependency alias."
        )
        raise TypeError(message)

    if len(markers) != 1 or len(metadata) != 1:
        message = "FromWeb[...] requires exactly one wired(...) metadata entry."
        raise TypeError(message)

    return annotation, markers[0]


def _build_adapter(model: _CallModel, /) -> _Factory:
    """Create a FastAPI-native adapter delegating to one Wireme call model.

    The adapter is an async generator function, so FastAPI enters it on the
    request-scoped exit stack: the resolved value stays alive until the
    response finishes and endpoint exceptions propagate into the factory.
    Generator factories are entered on the adapter's own stack, after any
    nested Wireme dependencies, so cleanup runs exactly once, in reverse
    order.
    """

    async def adapter(**kwargs: Any) -> AsyncIterator[Any]:
        async with AsyncExitStack() as stack:
            yield await model.asolve(
                stack=stack,
                cache_dependencies={},
                nested=True,
                **kwargs,
            )

    return adapter


@functools.cache
def _cached_bridge(
    factory: _Factory,
    use_cache: bool,
    /,
) -> _Factory:
    """Create one stable FastAPI adapter per factory and configuration."""
    model, public_signature = _factory_model(
        factory,
        use_cache=use_cache,
    )

    adapter = _build_adapter(model)
    typing.cast("_HasSignature", adapter).__signature__ = public_signature

    _bridges.setdefault(factory, {})[use_cache] = adapter

    return adapter


def _bridge_factory(
    factory: _Factory,
    use_cache: bool,
    /,
) -> _Factory:
    """Return the stable adapter for a factory after checking its identity."""
    try:
        hash(factory)
    except TypeError as error:
        message = (
            "FromWeb dependency factories must be hashable so bridged "
            "adapters keep a stable identity for caching and overrides. "
            "Wrap the factory in a function or give its class __hash__."
        )
        raise TypeError(message) from error

    return _cached_bridge(factory, use_cache)


def _bridge_marker(marker: _Dependant, /) -> _Factory:
    """Create or retrieve the adapter for a Wireme marker."""
    return _bridge_factory(marker.dependency, marker.use_cache)


def get_override_pairs(
    original: _Factory,
    replacement: _Factory,
    /,
) -> tuple[tuple[_Factory, _Factory], ...]:
    """Return direct and bridged FastAPI override pairs."""
    pairs: list[tuple[_Factory, _Factory]] = [
        (original, replacement),
    ]

    for use_cache, original_adapter in _bridges.get(original, {}).items():
        replacement_adapter = _bridge_factory(
            replacement,
            use_cache,
        )
        pairs.append((original_adapter, replacement_adapter))

    return tuple(pairs)


if TYPE_CHECKING:
    type FromWeb[T] = T

else:

    class FromWeb:
        """Create FastAPI annotations for classes and Wireme dependencies."""

        def __class_getitem__[T](
            cls,
            dependency: T,
            /,
        ) -> Any:
            """Build a FastAPI dependency annotation."""
            annotation, marker = _resolve_from_web_argument(dependency)

            if marker is None:
                return Annotated[
                    typing.cast("Any", annotation),
                    Depends(),
                ]

            adapter = _bridge_marker(marker)

            return Annotated[
                typing.cast("Any", annotation),
                Depends(
                    adapter,
                    use_cache=marker.use_cache,
                ),
            ]
