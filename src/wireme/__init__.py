"""Tiny, typed dependency injection that leaves values unchanged."""

from wireme._impl import Wired, override_dependency, wire, wired

__all__ = (
    "Wired",
    "override_dependency",
    "wire",
    "wired",
)
