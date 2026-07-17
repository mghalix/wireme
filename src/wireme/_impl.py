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
    Sequence,
)

from ._core import (
    _build_call_model,
    _CallModel,
    _CustomField,
    _Dependant,
    _Depends,
    _DiProvider,
    _inject,
)


class _HasSignature(typing.Protocol):
    """Represent a callable with a customizable runtime signature."""

    __signature__: inspect.Signature


__all__ = (
    "Wired",
    "_HasSignature",
    "_factory_model",
    "_wire",
    "override_dependency",
    "wire",
    "wired",
)

_MISSING = object()
_provider = _DiProvider()


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
    return bool(
        _dependency_markers(
            parameter,
            globalns=globalns,
            localns=localns,
        )
    )


def _dependency_markers(
    parameter: inspect.Parameter,
    /,
    *,
    globalns: dict[str, object],
    localns: dict[str, object],
) -> tuple[_Dependant, ...]:
    """Return all FastDepends dependency markers attached to a parameter."""
    markers: list[_Dependant] = []
    if isinstance(parameter.default, _Dependant):
        markers.append(parameter.default)

    annotation = _resolve_annotation(
        parameter.annotation,
        globalns=globalns,
        localns=localns,
    )
    if typing.get_origin(annotation) is typing.Annotated:
        markers.extend(
            metadata
            for metadata in typing.get_args(annotation)[1:]
            if isinstance(metadata, _Dependant)
        )

    return tuple(markers)


def _is_custom_field_parameter(
    parameter: inspect.Parameter,
    /,
    *,
    globalns: dict[str, object],
    localns: dict[str, object],
) -> bool:
    """Return whether a parameter opts into FastDepends CustomField behavior."""
    if isinstance(parameter.default, _CustomField):
        return True

    annotation = _resolve_annotation(
        parameter.annotation,
        globalns=globalns,
        localns=localns,
    )
    if typing.get_origin(annotation) is not typing.Annotated:
        return False

    return any(
        isinstance(metadata, _CustomField)
        for metadata in typing.get_args(annotation)[1:]
    )


def _caller_locals() -> dict[str, object]:
    """Capture best-effort locals from the frame calling a wiring entry point."""
    frame = inspect.currentframe()
    try:
        caller = (
            frame.f_back.f_back
            if frame is not None and frame.f_back is not None
            else None
        )
        return dict(caller.f_locals) if caller is not None else {}
    finally:
        del frame


def _analyze_signature(
    func: Callable[..., object],
    /,
    *,
    localns: dict[str, object],
    audited: set[int] | None = None,
) -> tuple[inspect.Signature, inspect.Signature, frozenset[str]]:
    """Return the original signature, resolved signature, and dependency names."""
    if audited is None:
        audited = set()
    audited.add(id(func))

    original_signature = inspect.signature(func)

    globalns = dict(getattr(func, "__globals__", {}))
    localns = localns | {
        parameter.__name__: parameter
        for parameter in getattr(func, "__type_params__", ())
    }

    resolved_parameters = tuple(
        parameter.replace(
            annotation=_resolve_annotation(
                parameter.annotation,
                globalns=globalns,
                localns=localns,
            )
        )
        for parameter in original_signature.parameters.values()
    )

    resolved_signature = original_signature.replace(
        parameters=resolved_parameters,
        return_annotation=_resolve_annotation(
            original_signature.return_annotation,
            globalns=globalns,
            localns=localns,
        ),
    )

    if any(
        _is_custom_field_parameter(
            parameter,
            globalns=globalns,
            localns=localns,
        )
        for parameter in resolved_parameters
    ):
        message = (
            "Wireme does not support FastDepends CustomField markers. "
            "Use wired(factory) to supply application-specific values "
            "through dependency injection."
        )
        raise TypeError(message)

    for parameter in resolved_parameters:
        for marker in _dependency_markers(
            parameter,
            globalns=globalns,
            localns=localns,
        ):
            factory = marker.dependency
            if id(factory) not in audited:
                _analyze_signature(
                    factory,
                    localns=localns,
                    audited=audited,
                )

    dependency_names = frozenset(
        parameter.name
        for parameter in resolved_parameters
        if _is_dependency_parameter(parameter, globalns=globalns, localns=localns)
    )

    return original_signature, resolved_signature, dependency_names


def _resolve_factory_signature(
    factory: Callable[..., object],
    /,
    *,
    localns: dict[str, object],
) -> None:
    """Expose resolved annotations so FastDepends sees dependency markers.

    Factories consumed as nested dependencies are inspected by FastDepends
    directly, and its resolver does not unwrap a PEP 695 alias hiding
    behind a postponed annotation. Resolving the signature once, when the
    factory is declared as a dependency, makes aliased dependencies work at
    any nesting depth. Callables that reject attribute assignment keep
    their raw signature.
    """
    _, resolved_signature, _ = _analyze_signature(factory, localns=localns)

    with contextlib.suppress(AttributeError, TypeError):
        typing.cast("_HasSignature", factory).__signature__ = resolved_signature


@contextlib.contextmanager
def _signature_override(
    func: Callable[..., object],
    signature: inspect.Signature,
    /,
) -> Generator[None, None, None]:
    """Temporarily expose a resolved signature to FastDepends."""
    previous_signature = getattr(func, "__signature__", _MISSING)
    typing.cast("_HasSignature", func).__signature__ = signature

    try:
        yield
    finally:
        if previous_signature is _MISSING:
            delattr(func, "__signature__")
        else:
            typing.cast("_HasSignature", func).__signature__ = typing.cast(
                "inspect.Signature",
                previous_signature,
            )


def _wire[**P, T](
    func: Callable[P, T],
    /,
    *,
    requires: tuple[Callable[..., object], ...] = (),
    localns: dict[str, object],
) -> Callable[P, T]:
    """Enable dependency injection and hide injected runtime parameters.

    Apply this decorator to functions and methods, not classes. ``localns``
    carries the decoration site's locals so annotations referencing local
    names resolve regardless of internal call depth.
    """
    for factory in requires:
        _resolve_factory_signature(factory, localns=localns)

    original_signature, resolved_signature, dependency_names = _analyze_signature(
        func,
        localns=localns,
    )

    with _signature_override(func, resolved_signature):
        wrapped = _inject(
            func,
            cast=False,
            cast_result=False,
            dependency_provider=_provider,
            extra_dependencies=tuple(
                _Depends(factory, cast=False, cast_result=False) for factory in requires
            ),
            serializer_cls=None,
        )

    public_parameters = tuple(
        parameter
        for parameter in original_signature.parameters.values()
        if parameter.name not in dependency_names
    )

    typing.cast("_HasSignature", wrapped).__signature__ = original_signature.replace(
        parameters=public_parameters
    )

    return wrapped


def _factory_model(
    factory: Callable[..., object],
    /,
    *,
    use_cache: bool,
) -> tuple[_CallModel, inspect.Signature]:
    """Build a FastDepends call model and the factory's public signature.

    The public signature hides injected parameters and carries resolved
    annotations so a consuming web framework can inspect it without access to
    the factory's globals. The model is built with ``is_sync=False`` because
    bridge adapters always resolve through ``asolve``.
    """
    _, resolved_signature, dependency_names = _analyze_signature(
        factory,
        localns=_caller_locals(),
    )

    with _signature_override(factory, resolved_signature):
        model = _build_call_model(
            factory,
            dependency_provider=_provider,
            use_cache=use_cache,
            is_sync=False,
            serializer_cls=None,
            serialize_result=False,
        )

    public_signature = resolved_signature.replace(
        parameters=tuple(
            parameter
            for parameter in resolved_signature.parameters.values()
            if parameter.name not in dependency_names
        ),
        return_annotation=inspect.Signature.empty,
    )

    return model, public_signature


def _wire_class[T](
    cls: type[T],
    /,
    *,
    requires: tuple[Callable[..., object], ...],
    localns: dict[str, object],
) -> type[T]:
    """Wire the constructor a class defines itself.

    Only the constructor is wired. Methods keep their own explicit ``@wire``
    so a reader can see exactly which calls resolve dependencies.
    """
    if "__init__" not in vars(cls):
        message = (
            f"wire applied to class {cls.__name__!r} requires the class to "
            "define __init__. Define __init__ with wired dependencies, or "
            "apply wire to individual methods."
        )
        raise TypeError(message)

    wired_init = _wire(
        cls.__init__,
        requires=requires,
        localns=localns,
    )
    typing.cast("typing.Any", cls).__init__ = wired_init

    return cls


def _wire_target(
    target: Callable[..., object],
    /,
    *,
    requires: tuple[Callable[..., object], ...],
    localns: dict[str, object],
) -> typing.Any:
    """Dispatch wiring to the class or callable implementation."""
    if inspect.isclass(target):
        return _wire_class(
            target,
            requires=requires,
            localns=localns,
        )

    return _wire(
        target,
        requires=requires,
        localns=localns,
    )


class _WireDecorator(typing.Protocol):
    """Decorate a class or callable while preserving its type."""

    @typing.overload
    def __call__[T](self, cls: type[T], /) -> type[T]: ...

    @typing.overload
    def __call__[**P, T](self, func: Callable[P, T], /) -> Callable[P, T]: ...


@typing.overload
def wire[T](func: type[T], /) -> type[T]: ...


@typing.overload
def wire[**P, T](func: Callable[P, T], /) -> Callable[P, T]: ...


@typing.overload
def wire(
    *,
    requires: Sequence[Callable[..., object]] = (),
) -> _WireDecorator: ...


def wire(
    func: Callable[..., object] | None = None,
    /,
    *,
    requires: Sequence[Callable[..., object]] = (),
) -> typing.Any:
    """Enable dependency injection and hide injected runtime parameters.

    Apply this decorator to a class, function, or method. On a class it
    wires the constructor the class defines; methods keep their own
    explicit decorator. Use it bare or with configuration:

        @wire
        class UserService: ...

        @wire(requires=(ensure_admin,))
        def operation(...): ...

    Args:
        func: The class or callable to wire when used as a bare decorator.
        requires: Side-effect dependency factories resolved on every call
            without being passed as parameters, such as guard checks.
            Generator factories clean up when the call finishes.

    Returns:
        The wired class or callable, or a decorator when used with
        configuration.

    Raises:
        TypeError: If applied to a class that does not define __init__.
        TypeError: If the target uses a FastDepends CustomField marker.
    """
    localns = _caller_locals()

    if func is None:

        def decorator(inner: Callable[..., object], /) -> typing.Any:
            return _wire_target(
                inner,
                requires=tuple(requires),
                localns=localns,
            )

        return decorator

    return _wire_target(
        func,
        requires=tuple(requires),
        localns=localns,
    )


@typing.overload
def wired[**P, R](
    factory: Callable[P, Awaitable[R]],
    /,
    *,
    use_cache: bool = True,
) -> R: ...


@typing.overload
def wired[**P, R](
    factory: Callable[P, AsyncIterator[R]],
    /,
    *,
    use_cache: bool = True,
) -> R: ...


@typing.overload
def wired[**P, R](
    factory: Callable[P, Iterator[R]],
    /,
    *,
    use_cache: bool = True,
) -> R: ...


@typing.overload
def wired[**P, R](
    factory: Callable[P, R],
    /,
    *,
    use_cache: bool = True,
) -> R: ...


def wired(
    factory: Callable[..., object],
    /,
    *,
    use_cache: bool = True,
) -> typing.Any:
    """Declare a dependency resolved by a callable.

    The factory's signature is resolved when the dependency is declared, so
    PEP 695 aliases and postponed annotations in the factory's own
    parameters work at any nesting depth.

    Raises:
        TypeError: If the factory uses a FastDepends CustomField marker.
    """
    _resolve_factory_signature(factory, localns=_caller_locals())

    return _Depends(
        factory,
        use_cache=use_cache,
        cast=False,
        cast_result=False,
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

    Raises:
        TypeError: If either factory uses a FastDepends CustomField marker.
    """
    localns = _caller_locals()
    _resolve_factory_signature(original, localns=localns)
    _resolve_factory_signature(replacement, localns=localns)

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
