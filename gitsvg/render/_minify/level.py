"""Minification level type — selects which post-processor steps run."""

from typing import Literal

MinifyLevel = Literal[0, 1, 2, 3]
"""Minification level selected by the CLI's `--small` flag.

- `0`: pristine drawsvg output (default).
- `1`: lossless basics — structural drops, whitespace strip, font-family
  hoist, 6dp rounding.
- `2`: L1 + hex shortening + 4dp rounding.
- `3`: L2 + font-fallback trim + 2dp rounding.
"""
