"""Internal implementation for :mod:`wireme`."""

from __future__ import annotations

import contextlib
import inspect
import typing
from collections.abc import (
    AsyncIterator,
    Awaitable,
    Callable,
    Generator,
    Iterator,
)

from ._core import _Dependant, _Depends, _inject, _Provider


class _HasSignature(typing.Protocol):
    """Represent a callable with a customizable runtime signature."""

    __signature__: inspect.Signature


_MISSING = object()
_provider = _Provider()


type _DependencyFactory[R] = (
    Callable[..., Awaitable[R]]
    | Callable[..., AsyncIterator[R]]
    | Callable[..., Iterator[R]]
    | Callable[..., R]
)


def Wired() -> typing.Any:
    """Mark an annotated dependency as optional for static type checkers."""
    return ...


def _resolve_annotation(
    annotation: object,
    /,
    *,
    globalns: dict[str, object],
    localns: dict[str, object],
) -> object:
    """Resolve strings and PEP 695 aliases recursively.

    Unresolved forward references become Any in FastDepends' internal
    signature while remaining unchanged in Wireme's public signature.
    """
    while True:
        if isinstance(annotation, str):
            try:
                annotation = eval(annotation, globalns, localns)  # noqa: S307
            except (AttributeError, NameError, TypeError):
                return typing.Any

            continue

        if isinstance(annotation, typing.TypeAliasType):
            annotation = annotation.__value__
            continue

        return annotation


def _is_dependency_parameter(
    parameter: inspect.Parameter,
    /,
    *,
    globalns: dict[str, object],
    localns: dict[str, object],
) -> bool:
    """Return whether a parameter is supplied through dependency injection."""
    if isinstance(parameter.default, _Dependant):
        return True

    annotation = _resolve_annotation(
        parameter.annotation,
        globalns=globalns,
        localns=localns,
    )
    if typing.get_origin(annotation) is not typing.Annotated:
        return False

    return any(
        isinstance(metadata, _Dependant) for metadata in typing.get_args(annotation)[1:]
    )


def wire[**P, T](func: Callable[P, T], /) -> Callable[P, T]:
    """Enable dependency injection and hide injected runtime parameters.

    Apply this decorator to functions and methods, not classes.
    """
    original_signature = inspect.signature(func)

    frame = inspect.currentframe()
    try:
        caller_locals = (
            dict(frame.f_back.f_locals)
            if frame is not None and frame.f_back is not None
            else {}
        )
    finally:
        del frame

    globalns = dict(getattr(func, "__globals__", {}))
    type_parameters = {
        parameter.__name__: parameter
        for parameter in getattr(func, "__type_params__", ())
    }
    caller_locals.update(type_parameters)

    resolved_parameters = tuple(
        parameter.replace(
            annotation=_resolve_annotation(
                parameter.annotation,
                globalns=globalns,
                localns=caller_locals,
            )
        )
        for parameter in original_signature.parameters.values()
    )

    resolved_signature = original_signature.replace(
        parameters=resolved_parameters,
        return_annotation=_resolve_annotation(
            original_signature.return_annotation,
            globalns=globalns,
            localns=caller_locals,
        ),
    )

    previous_signature = getattr(func, "__signature__", _MISSING)
    typing.cast("_HasSignature", func).__signature__ = resolved_signature

    try:
        wrapped = _inject(func, dependency_provider=_provider)
    finally:
        if previous_signature is _MISSING:
            delattr(func, "__signature__")
        else:
            typing.cast("_HasSignature", func).__signature__ = typing.cast(
                "inspect.Signature",
                previous_signature,
            )

    public_parameters = tuple(
        original_parameter
        for original_parameter, resolved_parameter in zip(
            original_signature.parameters.values(),
            resolved_signature.parameters.values(),
            strict=True,
        )
        if not _is_dependency_parameter(
            resolved_parameter,
            globalns=globalns,
            localns=caller_locals,
        )
    )

    typing.cast("_HasSignature", wrapped).__signature__ = original_signature.replace(
        parameters=public_parameters
    )

    return wrapped


@typing.overload
def wired[**P, R](
    factory: Callable[P, Awaitable[R]],
    /,
    *,
    use_cache: bool = True,
    cast: bool = True,
    cast_result: bool = False,
) -> R: ...


@typing.overload
def wired[**P, R](
    factory: Callable[P, AsyncIterator[R]],
    /,
    *,
    use_cache: bool = True,
    cast: bool = True,
    cast_result: bool = False,
) -> R: ...


@typing.overload
def wired[**P, R](
    factory: Callable[P, Iterator[R]],
    /,
    *,
    use_cache: bool = True,
    cast: bool = True,
    cast_result: bool = False,
) -> R: ...


@typing.overload
def wired[**P, R](
    factory: Callable[P, R],
    /,
    *,
    use_cache: bool = True,
    cast: bool = True,
    cast_result: bool = False,
) -> R: ...


def wired(
    factory: Callable[..., object],
    /,
    *,
    use_cache: bool = True,
    cast: bool = True,
    cast_result: bool = False,
) -> typing.Any:
    """Declare a dependency resolved by a callable."""
    return _Depends(
        factory,
        use_cache=use_cache,
        cast=cast,
        cast_result=cast_result,
    )


@contextlib.contextmanager
def override_dependency[R](
    original: _DependencyFactory[R],
    replacement: _DependencyFactory[R],
    /,
) -> Generator[None, None, None]:
    """Temporarily replace a dependency factory.

    Nested overrides are restored correctly. Overrides modify a shared provider,
    so use them for isolated tests and application setup, not concurrent
    request-level mutation.
    """
    previous_override = _provider.overrides.get(original, _MISSING)
    _provider.override(original, replacement)

    try:
        yield
    finally:
        if previous_override is _MISSING:
            _provider.overrides.pop(original, None)
        else:
            _provider.overrides[original] = typing.cast(
                "typing.Any",
                previous_override,
            )
