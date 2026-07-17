from __future__ import annotations

import inspect

import wireme

_EXPECTED_PUBLIC_API = (
    "Wired",
    "override_dependency",
    "wire",
    "wired",
)


def test_public_api() -> None:
    assert wireme.__all__ == _EXPECTED_PUBLIC_API


def test_validation_errors_are_not_exported() -> None:
    assert not hasattr(wireme, "ValidationError")
    assert not hasattr(wireme, "WiremeError")


def test_casting_options_are_not_supported() -> None:
    wire_parameters = inspect.signature(wireme.wire).parameters
    wired_parameters = inspect.signature(wireme.wired).parameters

    assert "cast" not in wire_parameters
    assert "cast_result" not in wire_parameters
    assert "cast" not in wired_parameters
    assert "cast_result" not in wired_parameters


def test_fastapi_integration_is_not_exported_from_root() -> None:
    assert "FromWeb" not in wireme.__all__
    assert "override_web_dependency" not in wireme.__all__
    assert not hasattr(wireme, "FromWeb")
    assert not hasattr(wireme, "override_web_dependency")
