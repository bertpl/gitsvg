"""Build the multi-theme preview SVG checked in as `examples/10_named_themes.svg`.

Reads `examples/10_named_themes.gitsvg.jsonl`, renders it once per
registered named theme, and tiles the per-theme SVGs into a single
labeled preview SVG. Rerun whenever themes change or when the
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
from gitsvg.theme._named_themes import NAMED_THEMES

# ==================================================================================================
#  Paths
# ==================================================================================================
REPO_ROOT = Path(__file__).resolve().parent.parent
INPUT_PATH = REPO_ROOT / "examples" / "10_named_themes.gitsvg.jsonl"
OUTPUT_PATH = REPO_ROOT / "examples" / "10_named_themes.svg"

# The `gui` theme is a table-layout theme, so it gets its own richer input
# (many branches + merges) and renders into a full-width tile of its own below
# the square grid, rather than sharing the compact `INPUT_PATH` diagram.
GUI_INPUT_PATH = REPO_ROOT / "examples" / "13_gui_table.gitsvg.jsonl"
GUI_THEME = "gui"


# ==================================================================================================
#  Themes to showcase
# ==================================================================================================
# Square-grid themes, in display order (row-major across the 2×2 grid).
# `default` and `muted` lead so the refresh and its escape hatch sit side by
# side. `gui` is shown separately as a full-width tile below the grid (see
# `GUI_THEME`), since its table layout wants the wider, richer diagram.
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
    showcase tile honors the user's authoring choices — only the
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
def _tile(d: draw.Drawing, name: str, inner: draw.Drawing, *, tile_x, tile_y_box, tile_width, tile_height) -> None:
    """Draw one labeled, bordered tile (label band + viewport + nested render) onto `d`.

    The nested render keeps its intrinsic aspect ratio: it is scaled down
    only if wider or taller than the padded viewport, then centered, so
    smaller renders sit centered at 1:1 and oversized ones fit without
    distortion.

    Args:
        d: The composition drawing to append onto.
        name: Theme name, shown centered in the label band above the tile.
        inner: The rendered per-theme drawing to nest.
        tile_x: Left edge of the bordered viewport.
        tile_y_box: Top edge of the bordered viewport (below the label band).
        tile_width: Bordered-viewport width.
        tile_height: Bordered-viewport height.
    """
    # --- label band ---------------------------
    d.append(
        draw.Text(
            name,
            font_size=_LABEL_FONT_SIZE,
            x=tile_x + tile_width / 2,
            y=tile_y_box - _LABEL_HEIGHT / 2,
            text_anchor="middle",
            dominant_baseline="middle",
            font_family="'Inter', 'Helvetica Neue', Helvetica, Arial, sans-serif",
            fill="#383838",
        )
    )

    # --- bordered viewport --------------------
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

    # --- nested render (fit + center) ---------
    avail_w = tile_width - 2 * _TILE_PADDING
    avail_h = tile_height - 2 * _TILE_PADDING
    scale = min(1.0, avail_w / inner.width, avail_h / inner.height)
    disp_w = inner.width * scale
    disp_h = inner.height * scale
    inner_x = tile_x + _TILE_PADDING + (avail_w - disp_w) / 2
    inner_y = tile_y_box + _TILE_PADDING + (avail_h - disp_h) / 2
    inner_svg = (
        f'<svg x="{inner_x}" y="{inner_y}" '
        f'width="{disp_w}" height="{disp_h}" '
        f'viewBox="0 0 {inner.width} {inner.height}">'
        f"{_inner_svg_content(inner.as_svg())}"
        f"</svg>"
    )
    d.append(draw.Raw(inner_svg))


def _build_preview(
    grid_themes: list[tuple[str, draw.Drawing]],
    wide_theme: tuple[str, draw.Drawing] | None = None,
) -> draw.Drawing:
    """Compose the grid themes into a square block, with an optional full-width tile below.

    `grid_themes` lay out in a squarish grid (`ceil(sqrt(n))` columns,
    row-major), every tile sized to the widest / tallest grid render so
    the block aligns. `wide_theme`, when present, is placed as a single
    tile spanning the full block width in a row beneath the grid — sized
    independently of the grid tiles, so it can never alter the grid block
    (the four square tiles stay pixel-for-pixel what they are without it).

    Args:
        grid_themes: `(theme_name, drawing)` pairs for the square grid.
        wide_theme: Optional `(theme_name, drawing)` for the full-width tile.

    Returns:
        A composed `Drawing` carrying the full tiled preview.
    """
    # --- grid-tile dimensions (grid renders only) ---
    tile_inner_width = max(d.width for _, d in grid_themes)
    tile_inner_height = max(d.height for _, d in grid_themes)
    tile_width = tile_inner_width + 2 * _TILE_PADDING
    tile_height = tile_inner_height + 2 * _TILE_PADDING
    cell_height = _LABEL_HEIGHT + tile_height  # label band + bordered viewport

    # --- grid shape ---------------------------
    n = len(grid_themes)
    n_cols = math.ceil(math.sqrt(n))
    n_rows = math.ceil(n / n_cols)

    content_width = n_cols * tile_width + (n_cols - 1) * _TILE_GAP
    grid_height = n_rows * cell_height + (n_rows - 1) * _TILE_GAP

    # --- wide-tile dimensions -----------------
    wide_block_height = 0
    if wide_theme is not None:
        wide_inner = wide_theme[1]
        wide_avail_w = content_width - 2 * _TILE_PADDING
        wide_scale = min(1.0, wide_avail_w / wide_inner.width)
        wide_tile_height = wide_inner.height * wide_scale + 2 * _TILE_PADDING
        wide_block_height = _TILE_GAP + _LABEL_HEIGHT + wide_tile_height

    # --- canvas dimensions --------------------
    canvas_width = 2 * _OUTER_MARGIN + content_width
    canvas_height = 2 * _OUTER_MARGIN + grid_height + wide_block_height

    d = draw.Drawing(canvas_width, canvas_height, origin=(0, 0))

    # --- grid tiles ---------------------------
    for i, (name, inner) in enumerate(grid_themes):
        col, row = i % n_cols, i // n_cols
        tile_x = _OUTER_MARGIN + col * (tile_width + _TILE_GAP)
        cell_y = _OUTER_MARGIN + row * (cell_height + _TILE_GAP)
        _tile(
            d,
            name,
            inner,
            tile_x=tile_x,
            tile_y_box=cell_y + _LABEL_HEIGHT,
            tile_width=tile_width,
            tile_height=tile_height,
        )

    # --- full-width tile ----------------------
    if wide_theme is not None:
        name, inner = wide_theme
        wide_tile_height = inner.height * wide_scale + 2 * _TILE_PADDING
        cell_y = _OUTER_MARGIN + grid_height + _TILE_GAP
        _tile(
            d,
            name,
            inner,
            tile_x=_OUTER_MARGIN,
            tile_y_box=cell_y + _LABEL_HEIGHT,
            tile_width=content_width,
            tile_height=wide_tile_height,
        )

    return d


# ==================================================================================================
#  Main
# ==================================================================================================
def _load_state(input_path: Path):
    """Parse, import-resolve, and apply a `.gitsvg.jsonl` file into render-ready state.

    Args:
        input_path: Path to the `.gitsvg.jsonl` source.

    Returns:
        The `(state, source_theme)` pair from `apply_ops`.

    Raises:
        SystemExit: If the input does not validate cleanly.
    """
    parsed_ops, report = parse_jsonl_file(input_path)
    parsed_ops = resolve_imports(parsed_ops, file=input_path, report=report)
    state, source_theme = apply_ops(parsed_ops, report)
    if not report.is_clean():
        raise SystemExit(f"{input_path.name} did not validate cleanly:\n{report}")
    return state, source_theme


def main() -> None:
    """Render the grid themes (shared input) + the `gui` tile (its own input) and write the preview."""
    for name in (*PREVIEW_THEMES, GUI_THEME):
        if name not in NAMED_THEMES:
            raise SystemExit(f"preview references unknown theme {name!r}; not in NAMED_THEMES")

    # --- square-grid themes (shared input) --
    grid_state, grid_source = _load_state(INPUT_PATH)
    grid = [(name, _render_through_theme(grid_state, grid_source, name)) for name in PREVIEW_THEMES]

    # --- gui tile (dedicated table input) ---
    gui_state, gui_source = _load_state(GUI_INPUT_PATH)
    gui_tile = (GUI_THEME, _render_through_theme(gui_state, gui_source, GUI_THEME))

    # --- compose + write --------------------
    preview = _build_preview(grid, gui_tile)
    preview.save_svg(str(OUTPUT_PATH))
    print(f"wrote {OUTPUT_PATH.relative_to(REPO_ROOT)} ({len(grid) + 1} themes)")


if __name__ == "__main__":
    main()
