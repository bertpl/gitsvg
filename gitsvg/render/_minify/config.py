"""Resolved minification settings derived from a `MinifyLevel`."""

from dataclasses import dataclass

from gitsvg.render._minify.level import MinifyLevel


@dataclass(frozen=True)
class MinifyConfig:
    """Per-step toggles + parameters derived from a `MinifyLevel`.

    Each step in the runner reads its own toggle (and parameters where
    applicable) to decide whether to execute. Resolved once per render
    via `compute_minify_config(level)`.
    """

    level: MinifyLevel

    # Step toggles (field order matches the runner's pinned execution order).
    drop_default_attrs: bool
    drop_empty_defs: bool
    hoist_font_family: bool
    trim_font_fallback: bool
    shorten_hex: bool
    round_numbers: bool
    extract_css_classes: bool
    strip_whitespace: bool

    # Step parameters.
    rounding_decimals: int


_ROUNDING_DECIMALS_BY_LEVEL: dict[MinifyLevel, int] = {0: 0, 1: 6, 2: 4, 3: 2}


def compute_minify_config(level: MinifyLevel) -> MinifyConfig:
    """Resolve a `MinifyLevel` to a populated `MinifyConfig`.

    See the `gitsvg.render._minify` package docstring for the level
    ladder. At L0 every toggle is off; the runner short-circuits and
    returns the input unchanged (the CLI bypasses the pipeline
    entirely at L0).

    Args:
        level: The minification level (0-3).

    Returns:
        A fully-populated `MinifyConfig`.
    """
    return MinifyConfig(
        level=level,
        drop_default_attrs=level >= 1,
        drop_empty_defs=level >= 1,
        hoist_font_family=level >= 1,
        trim_font_fallback=level >= 3,
        shorten_hex=level >= 2,
        round_numbers=level >= 1,
        extract_css_classes=level >= 2,
        strip_whitespace=level >= 1,
        rounding_decimals=_ROUNDING_DECIMALS_BY_LEVEL[level],
    )
