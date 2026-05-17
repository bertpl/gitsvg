.PHONY: help dev-setup build test format lint update-deps install release validate-local render-local refresh-examples rebuild-glyph-widths

help:
	@echo 'Commands:'
	@echo '  dev-setup      One-time: sync dev deps, install pre-commit hooks'
	@echo '  build          Build package'
	@echo '  test           Run pytest'
	@echo '  format         Format and fix with ruff'
	@echo '  lint           Ruff check'
	@echo '  update-deps    Re-resolve uv.lock to latest versions'
	@echo '  install        Re-install gitsvg stand-alone tool'
	@echo '  validate-local Validate every .gitsvg.jsonl under local/test_examples/'
	@echo '  render-local   Render every .gitsvg.jsonl under local/test_examples/ to SVG'
	@echo '  refresh-examples  Re-render every committed examples/*.gitsvg.jsonl, then rebuild the tiled themes preview'
	@echo '  rebuild-glyph-widths  Regenerate glyph-width LUTs from scripts/font_sources/'
	@echo '  release        Bump version, validate, tag, push (VERSION=X.Y.Z)'

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

validate-local:
	uv run python scripts/validate_local.py

render-local:
	uv run python scripts/render_local.py

# Re-render every committed example then rebuild the tiled themes preview.
# Order matters: the bulk loop would otherwise overwrite the tile via the
# indirect 10_named_themes.gitsvg.jsonl -> 10_named_themes.svg render, so the
# preview script runs at the end to restore the actual tile.
refresh-examples:
	@for f in examples/*.gitsvg.jsonl; do \
		base=$$(basename "$$f" .gitsvg.jsonl); \
		echo "rendering $$f -> examples/$$base.svg"; \
		uv run gitsvg render "$$f" -o "examples/$$base.svg" || exit 1; \
	done
	uv run python scripts/build_themed_preview.py

rebuild-glyph-widths:
	uv run python scripts/build_glyph_widths.py

release:
	@test -n "$(VERSION)" || (echo "Usage: make release VERSION=X.Y.Z" && exit 1)
	$(MAKE) test
	uv run python scripts/release.py $(VERSION)
