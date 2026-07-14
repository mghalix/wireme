set shell := ["bash", "-cu"]

default:
    @just --list

sync:
    uv sync --all-groups

format:
    uv run ruff format .
    uv run ruff check --fix .

check:
    uv run ruff format --check .
    uv run ruff check .
    uv run basedpyright
    uv run pytest --cov=wireme --cov-report=term-missing

build:
    rm -rf dist
    uv build --no-sources

smoke: build
    #!/usr/bin/env bash
    set -euo pipefail

    wheel="$(find dist -maxdepth 1 -name '*.whl' -print -quit)"
    sdist="$(find dist -maxdepth 1 -name '*.tar.gz' -print -quit)"

    uv run --isolated --no-project --with "$wheel" \
        python tests/smoke_test.py

    uv run --isolated --no-project --with "$sdist" \
        python tests/smoke_test.py

release-check: check smoke

release version:
    uv version {{ version }}
    just check
    just smoke
    git add pyproject.toml uv.lock
    git diff --cached --quiet || git commit -m "release: v{{ version }}"
    git tag -a "v{{ version }}" -m "v{{ version }}"
    git push origin HEAD --follow-tags
