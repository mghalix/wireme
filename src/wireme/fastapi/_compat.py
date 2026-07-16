"""Load the optional FastAPI dependency."""

from __future__ import annotations

try:
    from fastapi import Depends, FastAPI

except ModuleNotFoundError as error:  # pragma: no cover
    if error.name != "fastapi":
        raise

    message = (
        "wireme.fastapi is unavailable because the 'fastapi' extra is not "
        "installed. Install it with: uv add 'wireme[fastapi]'"
    )
    raise ModuleNotFoundError(message) from None


__all__ = (
    "Depends",
    "FastAPI",
)
