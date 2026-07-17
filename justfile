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

# Find unused Python code. Lower confidence to broaden the exploratory scan.
dead-code confidence="100":
    uv run vulture --min-confidence "{{ confidence }}"

# Audit GitHub Actions locally without requiring a GitHub token.
audit-actions persona="auditor" severity="low":
    uv run zizmor \
        --offline \
        --persona "{{ persona }}" \
        --min-severity "{{ severity }}" \
        .

# Install the repository-managed commit message hook.
hooks:
    uv run prek install --hook-type commit-msg

# Validate the hook configuration.
hooks-check:
    uv run prek validate-config .pre-commit-config.yaml

# Validate commits made after the selected base revision.
commits base="origin/main":
    uv run cz check --rev-range "{{ base }}..HEAD"

check:
    uv run ruff format --check .
    uv run ruff check .
    uv run basedpyright
    just hooks-check
    just dead-code
    just audit-actions
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
    uv run twine check dist/*
