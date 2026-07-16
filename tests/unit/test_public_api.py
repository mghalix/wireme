from __future__ import annotations

from fast_depends.exceptions import FastDependsError
from fast_depends.exceptions import ValidationError as FastDependsValidationError

import wireme
from wireme import ValidationError, WiremeError

_EXPECTED_PUBLIC_API = (
    "ValidationError",
    "Wired",
    "WiremeError",
    "override_dependency",
    "wire",
    "wired",
)


def test_public_api() -> None:
    assert wireme.__all__ == _EXPECTED_PUBLIC_API


def test_wireme_error_aliases_fast_depends_error() -> None:
    assert WiremeError is FastDependsError


def test_validation_error_is_reexported() -> None:
    assert ValidationError is FastDependsValidationError
    assert issubclass(ValidationError, WiremeError)


def test_fastapi_integration_is_not_exported_from_root() -> None:
    assert "FromWeb" not in wireme.__all__
    assert "override_web_dependency" not in wireme.__all__
    assert not hasattr(wireme, "FromWeb")
    assert not hasattr(wireme, "override_web_dependency")
