"""Isolate FastDepends imports behind one private boundary.

All FastDepends symbols used by Wireme enter through this module. Everything
imported here is part of the FastDepends public API (exported from package
``__init__`` modules), but the keyword contract of ``CallModel.solve`` and
``CallModel.asolve`` (``stack``, ``cache_dependencies``, ``nested``) is only
covered by tests, not documentation. The FastAPI bridge relies on it, so the
supported FastDepends range is constrained in pyproject.toml and regression
tests exercise the full lifecycle in tests/integration/fastapi.
"""

from typing import Final

from fast_depends import Depends as _Depends
from fast_depends import Provider as _Provider
from fast_depends import inject as _inject
from fast_depends.core import CallModel as _CallModel
from fast_depends.core import build_call_model as _build_call_model
from fast_depends.dependencies import Dependant as _Dependant
from fast_depends.pydantic import PydanticSerializer as _PydanticSerializer

_serializer: Final = _PydanticSerializer()

__all__ = (
    "_CallModel",
    "_Dependant",
    "_Depends",
    "_Provider",
    "_build_call_model",
    "_inject",
    "_serializer",
)
