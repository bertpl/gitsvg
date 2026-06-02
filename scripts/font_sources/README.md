# Font sources

This directory holds the source font binaries that
[`scripts/build_glyph_widths.py`](../build_glyph_widths.py) reads to
regenerate the per-character glyph-width LUTs under
[`gitsvg/render/_glyph_widths/`](../../gitsvg/render/_glyph_widths/).

Font binaries are gitignored; only this `README.md` and the local
`.gitignore` are tracked. The runtime `gitsvg` package ships the
derivative numeric tables, not the fonts themselves — these files
are needed only when regenerating the LUTs from updated upstream font
releases.

## Expected files

The build script looks for these filenames in this directory:

| Filename | Source |
|---|---|
| `Inter-Regular.ttf` | Inter, regular weight |
| `Inter-Bold.ttf` | Inter, bold weight |
| `DejaVuSans.ttf` | DejaVu Sans, regular weight |
| `DejaVuSans-Bold.ttf` | DejaVu Sans, bold weight |
| `DejaVuSansMono.ttf` | DejaVu Sans Mono, regular weight |
| `DejaVuSansMono-Bold.ttf` | DejaVu Sans Mono, bold weight |

## Where to obtain them

**Inter** — from the official releases at
<https://github.com/rsms/inter/releases>. Download the latest
`Inter-<version>.zip`, extract `extras/ttf/Inter-Regular.ttf` and
`extras/ttf/Inter-Bold.ttf` into this directory. Inter is distributed
under the SIL Open Font License 1.1.

**DejaVu Sans** and **DejaVu Sans Mono** — from the DejaVu project at
<https://dejavu-fonts.github.io/>. On many systems the TTF files are
already installed locally (e.g. TeX Live installs them under
`/usr/local/texlive/<year>/texmf-dist/fonts/truetype/public/dejavu/`
on macOS). DejaVu is distributed under the Bitstream Vera / DejaVu
license, which permits derivative works such as numeric width
tables.

## Regenerating the LUTs

Once all six font files are in place:

```
make rebuild-glyph-widths
```

This runs the build script under `uv run python` and rewrites each
LUT module under `gitsvg/render/_glyph_widths/`. Commit the resulting
changes alongside whatever bumped the source fonts.
