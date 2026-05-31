"""Build the multi-theme preview SVG checked in as `examples/10_named_themes.svg`.

Reads `examples/10_named_themes.gitsvg.jsonl`, renders it once per
registered named theme, and tiles the per-theme SVGs into a single
labelled preview SVG. Rerun whenever themes change or when the
underlying input file changes.

Usage::

    uv run python scripts/build_themed_preview.py
"""

import math
import re
from pathlib import Path

import drawsvg as draw

from gitsvg.imports import resolve_imports
from gitsvg.layout import compute_layout
from gitsvg.parse import parse_jsonl_file
from gitsvg.render import render
from gitsvg.state import apply_ops
from gitsvg.theme import Theme
from gitsvg.theme._apply import NAMED_THEMES

# ==================================================================================================
#  Paths
# ==================================================================================================
REPO_ROOT = Path(__file__).resolve().parent.parent
INPUT_PATH = REPO_ROOT / "examples" / "10_named_themes.gitsvg.jsonl"
OUTPUT_PATH = REPO_ROOT / "examples" / "10_named_themes.svg"


# ==================================================================================================
#  Themes to showcase
# ==================================================================================================
# Subset of `NAMED_THEMES` to include in the preview tile, in display order
# (row-major across the 2×2 grid). `default` and `muted` lead so the refresh
# and its escape hatch sit side by side. Extend this tuple when new themes
# ship; `_build_preview` lays them out in a grid that grows with the count.
PREVIEW_THEMES: tuple[str, ...] = ("default", "muted", "dark", "compact")


# ==================================================================================================
#  Tile layout constants
# ==================================================================================================
_TILE_GAP = 16  # horizontal gap between tiles, px
_TILE_PADDING = 8  # gap between border and rendered content, px
_LABEL_HEIGHT = 28  # vertical space reserved above each tile for its name
_LABEL_FONT_SIZE = 14  # px
_BORDER_COLOR = "#d4d4d4"
_BORDER_WIDTH = 1
_OUTER_MARGIN = 8  # outer padding around the whole composition, px


# ==================================================================================================
#  Per-theme render
# ==================================================================================================
def _render_through_theme(state, source_theme: Theme, theme_name: str) -> draw.Drawing:
    """Render the shared state through a single named theme.

    Per-branch overrides authored on the source diagram (`branch.color`,
    `branch.label_side`) are forwarded onto the named theme so each
    showcase tile honours the user's authoring choices — only the
    palette / typography / spacings differ between tiles.

    Args:
        state: The fully-applied diagram state (theme-independent).
        source_theme: The theme produced by the apply pass — carries
            the per-branch overrides authored on the source JSONL.
        theme_name: Name of a registered theme in `NAMED_THEMES`.

    Returns:
        The drawsvg `Drawing` for the named theme.
    """
    theme = NAMED_THEMES[theme_name].build({})
    theme.branch_color_overrides = dict(source_theme.branch_color_overrides)
    theme.branch_label_side_overrides = dict(source_theme.branch_label_side_overrides)
    layout_settings, renderer_settings = theme.split()
    layout = compute_layout(state, layout_settings)
    return render(layout, renderer_settings)


# ==================================================================================================
#  SVG inner-content extraction
# ==================================================================================================
_SVG_OUTER_TAG_RE = re.compile(r"<svg[^>]*>", re.IGNORECASE)


def _inner_svg_content(svg_text: str) -> str:
    """Strip the outer `<svg ...>...</svg>` so the content can nest under another viewport.

    Args:
        svg_text: Full SVG document as produced by `Drawing.as_svg()`.

    Returns:
        The content between the opening `<svg>` and closing `</svg>` tags.
    """
    # --- strip XML declaration --------------
    start = svg_text.find("<svg")
    if start == -1:
        raise ValueError("no <svg> tag in input")
    after_open = _SVG_OUTER_TAG_RE.search(svg_text, start)
    if after_open is None:
        raise ValueError("could not parse <svg> opening tag")
    inner_start = after_open.end()
    inner_end = svg_text.rfind("</svg>")
    if inner_end == -1:
        raise ValueError("no </svg> closing tag")
    return svg_text[inner_start:inner_end].strip()


# ==================================================================================================
#  Compose tiles
# ==================================================================================================
def _build_preview(themes: list[tuple[str, draw.Drawing]]) -> draw.Drawing:
    """Tile the per-theme drawings into one labelled preview SVG.

    Tiles sit in a squarish grid (`ceil(sqrt(n))` columns, row-major in
    display order), each consisting of a centered label above a bordered
    viewport containing the rendered diagram. Every tile is sized to the
    widest / tallest per-theme render so the grid aligns; shorter renders
    sit centered inside their tile. Four themes lay out as a 2×2 grid.

    Args:
        themes: List of `(theme_name, drawing)` pairs in display order.

    Returns:
        A composed `Drawing` carrying the full tiled preview.
    """
    # --- per-tile dimensions ------------------
    tile_inner_width = max(d.width for _, d in themes)
    tile_inner_height = max(d.height for _, d in themes)
    tile_width = tile_inner_width + 2 * _TILE_PADDING
    tile_height = tile_inner_height + 2 * _TILE_PADDING
    cell_height = _LABEL_HEIGHT + tile_height  # label band + bordered viewport

    # --- grid shape ---------------------------
    n = len(themes)
    n_cols = math.ceil(math.sqrt(n))
    n_rows = math.ceil(n / n_cols)

    # --- canvas dimensions --------------------
    canvas_width = 2 * _OUTER_MARGIN + n_cols * tile_width + (n_cols - 1) * _TILE_GAP
    canvas_height = 2 * _OUTER_MARGIN + n_rows * cell_height + (n_rows - 1) * _TILE_GAP

    d = draw.Drawing(canvas_width, canvas_height, origin=(0, 0))

    # --- per-tile placement -------------------
    for i, (name, inner) in enumerate(themes):
        col, row = i % n_cols, i // n_cols
        tile_x = _OUTER_MARGIN + col * (tile_width + _TILE_GAP)
        cell_y = _OUTER_MARGIN + row * (cell_height + _TILE_GAP)
        tile_y_label = cell_y + _LABEL_HEIGHT / 2
        tile_y_box = cell_y + _LABEL_HEIGHT

        # Label (centered above the tile).
        d.append(
            draw.Text(
                name,
                font_size=_LABEL_FONT_SIZE,
                x=tile_x + tile_width / 2,
                y=tile_y_label,
                text_anchor="middle",
                dominant_baseline="middle",
                font_family="'Inter', 'Helvetica Neue', Helvetica, Arial, sans-serif",
                fill="#383838",
            )
        )

        # Border rect around the rendered viewport.
        d.append(
            draw.Rectangle(
                tile_x,
                tile_y_box,
                tile_width,
                tile_height,
                stroke=_BORDER_COLOR,
                stroke_width=_BORDER_WIDTH,
                fill="none",
            )
        )

        # Nested SVG containing the rendered content. Use the inner
        # drawing's intrinsic dimensions as the viewBox so the diagram
        # scales 1:1 inside the bordered viewport, centered within the
        # padded area so smaller themes don't anchor to the top-left.
        inner_x = tile_x + _TILE_PADDING + (tile_inner_width - inner.width) / 2
        inner_y = tile_y_box + _TILE_PADDING + (tile_inner_height - inner.height) / 2
        inner_svg = (
            f'<svg x="{inner_x}" y="{inner_y}" '
            f'width="{inner.width}" height="{inner.height}" '
            f'viewBox="0 0 {inner.width} {inner.height}">'
            f"{_inner_svg_content(inner.as_svg())}"
            f"</svg>"
        )
        d.append(draw.Raw(inner_svg))

    return d


# ==================================================================================================
#  Main
# ==================================================================================================
def main() -> None:
    """Render every named theme over the shared input and write the tiled preview SVG."""
    # --- parse + apply --------------------
    parsed_ops, report = parse_jsonl_file(INPUT_PATH)
    parsed_ops = resolve_imports(parsed_ops, file=INPUT_PATH, report=report)
    state, source_theme = apply_ops(parsed_ops, report)
    if not report.is_clean():
        raise SystemExit(f"input did not validate cleanly:\n{report}")

    # --- render per theme in display order --
    rendered: list[tuple[str, draw.Drawing]] = []
    for name in PREVIEW_THEMES:
        if name not in NAMED_THEMES:
            raise SystemExit(f"PREVIEW_THEMES references unknown theme {name!r}; not in NAMED_THEMES")
        rendered.append((name, _render_through_theme(state, source_theme, name)))

    # --- compose + write --------------------
    preview = _build_preview(rendered)
    preview.save_svg(str(OUTPUT_PATH))
    print(f"wrote {OUTPUT_PATH.relative_to(REPO_ROOT)} ({len(rendered)} themes)")


if __name__ == "__main__":
    main()
