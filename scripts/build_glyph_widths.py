"""Generate glyph-width LUT modules from bundled font sources.

Reads source fonts from ``scripts/font_sources/`` and writes one
Python module per (font, weight) combination under
``gitsvg/render/_glyph_widths/``. Each module exposes a ``WIDTHS``
dict mapping each measured character to its advance width in em-units
(width per ``font_size = 1``). Pixel width = em-width × font_size.

Run manually via ``make rebuild-glyph-widths`` when the source fonts
under ``scripts/font_sources/`` change; not part of ``make test`` or
CI. ``fonttools`` is a dev-only dependency.
"""

import string
from datetime import date
from pathlib import Path
from typing import NamedTuple

from fontTools.ttLib import TTFont

REPO_ROOT = Path(__file__).resolve().parent.parent
FONT_SOURCES_DIR = REPO_ROOT / "scripts" / "font_sources"
LUT_OUTPUT_DIR = REPO_ROOT / "gitsvg" / "render" / "_glyph_widths"

# Characters measured per font: ASCII printable minus the non-rendering
# whitespace (`\t\n\r\x0b\x0c`). Covers digits, letters, all ASCII
# punctuation, and the literal space. ~95 entries per LUT.
CHARSET: str = string.digits + string.ascii_letters + string.punctuation + " "


# ==================================================================================================
#  Font specs — one entry per output LUT module
# ==================================================================================================
class FontSpec(NamedTuple):
    """Describes one source font and its derived LUT module."""

    source_filename: str
    output_module: str
    display_name: str
    license_note: str


FONT_SPECS: list[FontSpec] = [
    FontSpec(
        source_filename="Inter-Regular.ttf",
        output_module="inter_regular",
        display_name="Inter Regular",
        license_note="Inter (https://github.com/rsms/inter), SIL Open Font License 1.1.",
    ),
    FontSpec(
        source_filename="Inter-Bold.ttf",
        output_module="inter_bold",
        display_name="Inter Bold",
        license_note="Inter (https://github.com/rsms/inter), SIL Open Font License 1.1.",
    ),
    FontSpec(
        source_filename="DejaVuSans.ttf",
        output_module="sans_serif_regular",
        display_name="DejaVu Sans Regular (represents the `sans-serif` generic family)",
        license_note="DejaVu Sans (https://dejavu-fonts.github.io/), Bitstream Vera / DejaVu Fonts License.",
    ),
    FontSpec(
        source_filename="DejaVuSans-Bold.ttf",
        output_module="sans_serif_bold",
        display_name="DejaVu Sans Bold (represents the `sans-serif` generic family, bold weight)",
        license_note="DejaVu Sans (https://dejavu-fonts.github.io/), Bitstream Vera / DejaVu Fonts License.",
    ),
    FontSpec(
        source_filename="DejaVuSansMono.ttf",
        output_module="monospace_regular",
        display_name="DejaVu Sans Mono Regular (represents the `monospace` generic family)",
        license_note="DejaVu Sans Mono (https://dejavu-fonts.github.io/), Bitstream Vera / DejaVu Fonts License.",
    ),
    FontSpec(
        source_filename="DejaVuSansMono-Bold.ttf",
        output_module="monospace_bold",
        display_name="DejaVu Sans Mono Bold (represents the `monospace` generic family, bold weight)",
        license_note="DejaVu Sans Mono (https://dejavu-fonts.github.io/), Bitstream Vera / DejaVu Fonts License.",
    ),
]


# ==================================================================================================
#  Glyph measurement
# ==================================================================================================
def measure_widths(font_path: Path, charset: str) -> dict[str, float]:
    """Measure per-character advance widths for `charset` in em-units.

    Args:
        font_path: Path to the source font file (.ttf or .otf).
        charset: Characters to measure.

    Returns:
        Char → em-width mapping. Pixel width = value × font_size.
        Characters absent from the font's cmap are silently skipped.
    """
    font = TTFont(font_path)
    upem = font["head"].unitsPerEm
    cmap = font.getBestCmap()
    hmtx = font["hmtx"]

    widths: dict[str, float] = {}
    for char in charset:
        glyph_name = cmap.get(ord(char))
        if glyph_name is None:
            continue
        advance_fu, _ = hmtx[glyph_name]
        widths[char] = advance_fu / upem
    return widths


# ==================================================================================================
#  LUT module emission
# ==================================================================================================
def render_module(spec: FontSpec, widths: dict[str, float], generation_date: str) -> str:
    """Render the Python source for one LUT module.

    Args:
        spec: Identifies the source font and output module.
        widths: Char → em-width mapping returned by `measure_widths`.
        generation_date: Date string recorded in the docstring.

    Returns:
        Full Python source ready to write to disk.
    """
    body_lines = ["WIDTHS: dict[str, float] = {"]
    for char in sorted(widths):
        body_lines.append(f"    {char!r}: {widths[char]:.6f},")
    body_lines.append("}")
    body = "\n".join(body_lines)
    return (
        f'"""Glyph-width LUT — {spec.display_name}.\n'
        f"\n"
        f"Generated by ``scripts/build_glyph_widths.py`` on {generation_date}.\n"
        f"Source font: {spec.license_note}\n"
        f"\n"
        f"Widths are em-units — pixel width = value × font_size.\n"
        f'"""\n'
        f"\n"
        f"{body}\n"
    )


# ==================================================================================================
#  Driver
# ==================================================================================================
def main() -> None:
    """Regenerate every LUT module from the bundled source fonts."""
    LUT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    for spec in FONT_SPECS:
        font_path = FONT_SOURCES_DIR / spec.source_filename
        if not font_path.exists():
            raise SystemExit(f"missing source font: {font_path}")
        widths = measure_widths(font_path, CHARSET)
        output_path = LUT_OUTPUT_DIR / f"{spec.output_module}.py"
        output_path.write_text(render_module(spec, widths, today))
        print(f"  [{spec.output_module}.py] {len(widths)} glyphs from {spec.source_filename}")


if __name__ == "__main__":
    main()
