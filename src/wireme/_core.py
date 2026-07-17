"""Isolate FastDepends imports behind one private boundary.

All FastDepends symbols used by Wireme enter through this module. Everything
imported here is part of the FastDepends public API (exported from package
``__init__`` modules), but the keyword contract of ``CallModel.solve`` and
``CallModel.asolve`` (``stack``, ``cache_dependencies``, ``nested``) and the
``Provider`` model dictionaries are only covered by tests, not documentation.
The FastAPI bridge and serializer-free override path rely on those contracts,
so the supported FastDepends range is constrained in pyproject.toml and
regression tests exercise both paths.
"""

from collections.abc import Callable
from typing import Any

from fast_depends import Depends as _Depends
from fast_depends import Provider as _Provider
from fast_depends import inject as _inject
from fast_depends.core import CallModel as _CallModel
from fast_depends.core import build_call_model as _build_call_model
from fast_depends.dependencies import Dependant as _Dependant
from fast_depends.library import CustomField as _CustomField


class _DiProvider(_Provider):
    """Build every override model without an upstream serializer."""

    def override(
        self,
        original: Callable[..., Any],
        override: Callable[..., Any],
    ) -> None:
        """Install an override while preserving Wireme's DI-only contract."""
        if original not in self.dependencies:
            self.dependencies[original] = _build_call_model(
                original,
                dependency_provider=self,
                serializer_cls=None,
                serialize_result=False,
            )

        self.overrides[original] = _build_call_model(
            override,
            dependency_provider=self,
            serializer_cls=None,
            serialize_result=False,
        )


__all__ = (
    "_CallModel",
    "_CustomField",
    "_Dependant",
    "_Depends",
    "_DiProvider",
    "_build_call_model",
    "_inject",
)
