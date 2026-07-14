"""Tiny, typed dependency injection built on FastDepends."""

from wireme._errors import ValidationError, WiremeError
from wireme._impl import Wired, override_dependency, wire, wired

__all__ = (
    "ValidationError",
    "Wired",
    "WiremeError",
    "override_dependency",
    "wire",
    "wired",
)
