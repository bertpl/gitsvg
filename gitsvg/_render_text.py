"""Public text-to-SVG entry point for the gitsvg library.

`render_text` is the stable, documented way for an external consumer
(a docs site, the mkdocs plugin) to turn a JSONL op-stream *string* into
an inline-embeddable SVG *string* without composing pipeline internals.
It is the text twin of the CLI's file-based render path, ending in an
SVG serialized for inlining into HTML — no XML prolog, no injected
`<style>` / `<script>`.

Re-exported from the package root (`gitsvg.render_text`,
`gitsvg.GitsvgValidationError`, `gitsvg.ValidationReport`); this module
holds the implementation so `gitsvg/__init__.py` stays thin.
"""

from pathlib import Path

from ._pipeline import apply_and_validate
from .errors import ValidationReport
from .imports import resolve_imports
from .layout import compute_layout
from .parse import parse_jsonl_text
from .render import render

# Source label for in-memory input: stands in for a file path in error
# locations. In-memory input has no directory for imports to resolve
# against, so import resolution runs with `allow_imports=False`.
_TEXT_INPUT_LABEL = "<input>"


class GitsvgValidationError(Exception):
    """Raised by `render_text` when the input op-stream fails validation.

    Carries the full `ValidationReport` so callers can render the
    individual errors however they like (each entry has a `.format()`).

    Attributes:
        report: The non-clean report that triggered the error.
    """

    def __init__(self, report: ValidationReport) -> None:
        """Build the error from a non-clean report, summarizing its entries."""
        self.report = report
        count = len(report)
        plural = "error" if count == 1 else "errors"
        details = "\n".join(error.format() for error in report.errors)
        super().__init__(f"input failed validation with {count} {plural}:\n{details}")


def render_text(source: str, *, id_prefix: str = "") -> str:
    """Render a JSONL op-stream string to an inline-embeddable SVG string.

    Runs the same validate-and-render pipeline as `gitsvg render`, but on
    an in-memory string and returning the SVG as a string rather than
    writing a file. The output omits the XML prolog and any injected
    `<style>` / `<script>`, and the root `<svg>` carries its `xmlns`, so
    the result inlines directly into an HTML document.

    Args:
        source: The op-stream as `.gitsvg.jsonl` text (one JSON op per
            line). An `import` op is rejected (error `E306`) — in-memory
            input has no directory to resolve imports against; inline
            the imported ops instead.
        id_prefix: Optional prefix for element ids in the emitted SVG, so
            multiple inline diagrams on one page can't collide. Empty
            (the default) keeps drawsvg's default prefix.

    Returns:
        The SVG document as a string, ready to inline into HTML.

    Raises:
        GitsvgValidationError: If `source` fails to parse or validate. No
            partial SVG is produced; the attached `report` carries the
            individual errors.
    """
    parsed_ops, report = parse_jsonl_text(source, file=_TEXT_INPUT_LABEL)
    expanded_ops = resolve_imports(parsed_ops, file=Path(_TEXT_INPUT_LABEL), report=report, allow_imports=False)
    state, theme = apply_and_validate(expanded_ops, report)
    if not report.is_clean():
        raise GitsvgValidationError(report)

    layout_settings, renderer_settings = theme.split()
    layout = compute_layout(state, layout_settings)
    drawing = render(layout, renderer_settings)
    if id_prefix:
        drawing.id_prefix = id_prefix
    return drawing.as_svg(header="", skip_css=True, skip_js=True)
