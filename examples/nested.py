"""Nested factories and per-call caching.

Factories can depend on other factories. A dependency resolves once per
wired call by default, even when several factories share it. Disable the
cache per declaration when every use must create a new value.
"""

from __future__ import annotations

from wireme import wire, wired

calls: list[str] = []


class Settings:
    database_url = "postgres://production"


class Database:
    def __init__(self, url: str) -> None:
        self.url = url


def get_settings() -> Settings:
    calls.append("settings")
    return Settings()


def get_database(*, settings: Settings = wired(get_settings)) -> Database:
    calls.append("database")
    return Database(settings.database_url)


@wire
def report(
    *,
    database: Database = wired(get_database),
    settings: Settings = wired(get_settings),
) -> str:
    return f"{database.url} ({settings.database_url})"


def make_token() -> object:
    calls.append("token")
    return object()


@wire
def tokens_differ(
    *,
    first: object = wired(make_token, use_cache=False),
    second: object = wired(make_token, use_cache=False),
) -> bool:
    return first is not second


if __name__ == "__main__":
    assert report() == "postgres://production (postgres://production)"
    assert calls == ["settings", "database"]  # settings resolved once

    calls.clear()
    assert tokens_differ()
    assert calls == ["token", "token"]  # cache disabled, resolved twice
    print("shared dependencies resolve once per call unless uncached")
