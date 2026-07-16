"""Verify that importing the FastAPI integration gives a useful error."""

from __future__ import annotations

import importlib

_EXPECTED_MESSAGE = (
    "wireme.fastapi is unavailable because the 'fastapi' extra is not "
    "installed. Install it with: uv add 'wireme[fastapi]'"
)


try:
    importlib.import_module("wireme.fastapi")

except ModuleNotFoundError as error:
    assert str(error) == _EXPECTED_MESSAGE

else:
    message = "Expected importing wireme.fastapi without its extra to fail."
    raise AssertionError(message)


print("wireme FastAPI missing-extra smoke test passed")
