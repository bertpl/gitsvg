.PHONY: help dev-setup build test format lint update-deps install release

help:
	@echo 'Commands:'
	@echo '  dev-setup   One-time: sync dev deps, install pre-commit hooks'
	@echo '  build       Build package'
	@echo '  test        Run pytest'
	@echo '  format      Format and fix with ruff'
	@echo '  lint        Ruff check'
	@echo '  update-deps Re-resolve uv.lock to latest versions'
	@echo '  install     Re-install gitsvg stand-alone tool'
	@echo '  release     Bump version, validate, tag, push (VERSION=X.Y.Z)'

dev-setup:
	uv sync --group dev
	uv run pre-commit install

build:
	uv build

test:
	uv run pytest

format:
	uv run ruff format gitsvg tests scripts
	uv run ruff check --fix gitsvg tests scripts

lint:
	uv run ruff check gitsvg tests scripts

update-deps:
	uv lock --upgrade

install:
	uv tool install --editable .

release:
	@test -n "$(VERSION)" || (echo "Usage: make release VERSION=X.Y.Z" && exit 1)
	$(MAKE) test
	uv run python scripts/release.py $(VERSION)
