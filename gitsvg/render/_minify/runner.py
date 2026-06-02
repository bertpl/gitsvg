"""The `minify(...)` entry point that drives the post-processor pipeline.

Step ordering is fixed (not data-driven). The pinned order:

1. `drop_default_attribute_values` — clean defaults first so subsequent
   steps don't extract or hoist them.
2. `drop_empty_defs_and_unused_xlink` — remove empty `<defs>` and
   unused xlink. (Future symbol/use dedup may re-populate `<defs>`.)
3. `hoist_font_family_to_root` — consolidate `font-family` onto the
   root, before any trim or extraction sees it.
4. `trim_font_family_fallback` — operates on the consolidated root
   attribute; L3 only.
5. `shorten_hex_colors` — color-attribute substitution.
6. `round_numbers` — coordinates are stable by now; runs before CSS
   class extraction so values packed into the `<style>` block are
   already at the level's target precision (the rounding regex
   targets quoted attribute values only and would otherwise miss the
   CSS-property syntax).
7. `extract_css_classes` — hoist repeated presentation clusters into
   a `<style>` block; L2+.
8. *(reserved)* `<symbol>` + `<use>` dedup — slot for the L2+ step.
9. `strip_inter_element_whitespace` — purely cosmetic, runs last.

Most adjacencies are order-independent but pinned for determinism.
The few real dependencies: defaults-drop before CSS extraction (so
defaults aren't hoisted); hex/rounding before CSS extraction (so
extracted values are already normalized); empty-defs drop before
symbol/use (so a populated `<defs>` from dedup isn't accidentally
dropped); font-family hoist before font-fallback trim.
"""

from gitsvg.render._minify._steps import (
    drop_default_attribute_values,
    drop_empty_defs_and_unused_xlink,
    extract_css_classes,
    hoist_font_family_to_root,
    round_numbers,
    shorten_hex_colors,
    strip_inter_element_whitespace,
    trim_font_family_fallback,
)
from gitsvg.render._minify.config import MinifyConfig
from gitsvg.render._renderer_settings import RendererSettings


def minify(svg: str, config: MinifyConfig, theme: RendererSettings) -> str:
    """Apply the minification pipeline steps enabled by `config`.

    L0 returns input unchanged (the runner short-circuits — the CLI
    bypasses the pipeline at L0, but a direct call still behaves
    correctly). L1+ runs the enabled subset in the pinned step order
    documented at the top of this module.

    Args:
        svg: The full SVG markup as a string.
        config: Resolved level-derived step toggles + parameters.
        theme: Resolved renderer theme — supplies the font-family
            values the trim step compares against.

    Returns:
        The (potentially) reduced SVG markup.
    """
    if config.level == 0:
        return svg
    if config.drop_default_attrs:
        svg = drop_default_attribute_values(svg)
    if config.drop_empty_defs:
        svg = drop_empty_defs_and_unused_xlink(svg)
    if config.hoist_font_family:
        svg = hoist_font_family_to_root(svg)
    if config.trim_font_fallback:
        svg = trim_font_family_fallback(svg, theme)
    if config.shorten_hex:
        svg = shorten_hex_colors(svg)
    if config.round_numbers:
        svg = round_numbers(svg, decimals=config.rounding_decimals)
    if config.extract_css_classes:
        svg = extract_css_classes(svg)
    if config.strip_whitespace:
        svg = strip_inter_element_whitespace(svg)
    return svg
