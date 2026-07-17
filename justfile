set shell := ["bash", "-euo", "pipefail", "-c"]

default:
    @just --list

# Remove python tool caches and build artifacts.
clean:
    ./scripts/clean

test-unit:
    uv run pytest tests/unit

test-integration:
    uv run pytest tests/integration -m integration

test-automation:
    uv run pytest tests/automation

test:
    uv run pytest \
        tests/unit \
        tests/integration \
        tests/automation \
        --cov=wireme \
        --cov-report=term-missing

check:
    uv run ruff format --check .
    uv run ruff check .
    uv run basedpyright
    uv run pytest \
        tests/unit \
        tests/integration \
        tests/automation \
        --cov=wireme \
        --cov-report=term-missing

examples:
    ./scripts/examples

build:
    rm -rf dist
    uv build --no-sources

smoke-wheel: build
    ./scripts/smoke "$(find dist -maxdepth 1 -name '*.whl' -print -quit)"

smoke-sdist: build
    ./scripts/smoke "$(find dist -maxdepth 1 -name '*.tar.gz' -print -quit)"

smoke: build
    ./scripts/smoke "$(find dist -maxdepth 1 -name '*.whl' -print -quit)"
    ./scripts/smoke "$(find dist -maxdepth 1 -name '*.tar.gz' -print -quit)"

# Serve the docs site locally with live reload (opens the browser).
docs:
    cd website && uvx --with-requirements requirements.txt zensical serve -o

# Build the docs site into website/site.
docs-build:
    cd website && uvx --with-requirements requirements.txt zensical build --strict

release-check: check examples docs-build smoke
