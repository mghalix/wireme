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

test:
    uv run pytest \
        tests/unit \
        tests/integration \
        --cov=wireme \
        --cov-report=term-missing

check:
    uv run ruff format --check .
    uv run ruff check .
    uv run basedpyright
    uv run pytest \
        tests/unit \
        tests/integration \
        --cov=wireme \
        --cov-report=term-missing

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
    cd website && uvx zensical serve -o

# Build the docs site into website/site.
docs-build:
    cd website && uvx zensical build --strict

release-check: check smoke

release version:
    uv version {{ version }}
    just check
    just smoke
    git add pyproject.toml uv.lock
    git diff --cached --quiet || git commit -m "release: v{{ version }}"
    git tag -a "v{{ version }}" -m "v{{ version }}"
    git push origin HEAD --follow-tags
