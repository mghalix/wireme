"""Process-wide singletons through named factories.

Create the instance at module scope when it must fail fast at import time,
or cache the factory when lazy creation is fine. Either way the factory is
a named function, so override_dependency can target it.
"""

from __future__ import annotations

import functools
from typing import Annotated

from wireme import Wired, override_dependency, wire, wired


class Settings:
    def __init__(self, environment: str = "production") -> None:
        self.environment = environment


settings = Settings()  # validates configuration once, at import time


def get_settings() -> Settings:
    return settings


type SettingsDep = Annotated[Settings, wired(get_settings)]


@functools.cache
def get_lazy_settings() -> Settings:
    return Settings()


@wire
def describe_environment(*, config: SettingsDep = Wired()) -> str:
    return config.environment


if __name__ == "__main__":
    assert describe_environment() == "production"
    assert get_lazy_settings() is get_lazy_settings()

    def get_test_settings() -> Settings:
        return Settings("test")

    with override_dependency(get_settings, get_test_settings):
        assert describe_environment() == "test"

    assert describe_environment() == "production"
    print("one instance per process, overrides still work")
