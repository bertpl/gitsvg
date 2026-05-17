"""DOM-equivalence helper for testing visually-lossless minification steps.

Compares two SVGs by parsing both, normalising into a canonical form,
and asserting the canonical strings match. Normalisations cover every
L0 ↔ L1 ↔ L2 transform in the pipeline:

- XML declaration stripped.
- Empty `<defs>` elements removed.
- `xmlns:*` namespace declarations ignored (serialiser skips them).
- Default attribute values dropped (e.g. `font-weight="400"`).
- Hex colours expanded to long form (`#abc` → `#aabbcc`).
- Numeric attribute values rounded to 1dp; sub-pixel differences are
  well below the visually-lossless contract under typical screen
  viewing conditions.
- Inheriting presentation attributes pushed down to leaf elements
  (so a hoisted `font-family` on `<svg>` matches a per-`<text>`
  attribute).
- Element attributes sorted alphabetically; inter-element whitespace
  collapsed.

Stdlib only — no lxml dependency.
"""

import re
import xml.etree.ElementTree as ET

# Presentation attributes that inherit per the SVG spec. Restricted to
# the ones that matter for gitsvg's render output today.
_INHERITING_ATTRS: frozenset[str] = frozenset(
    {
        "fill",
        "stroke",
        "stroke-width",
        "stroke-dasharray",
        "stroke-linecap",
        "stroke-linejoin",
        "stroke-opacity",
        "fill-opacity",
        "font-family",
        "font-size",
        "font-weight",
        "font-style",
        "text-anchor",
        "color",
    }
)

# Inheriting attributes that only affect text-rendering elements. After
# push-down, these get spuriously written onto drawable leaves like
# `<path>`; we strip them via `_filter_irrelevant_inherited_attrs`.
_TEXT_ONLY_INHERITING_ATTRS: frozenset[str] = frozenset(
    {"font-family", "font-size", "font-weight", "font-style", "text-anchor"}
)
_TEXT_RENDERING_TAGS: frozenset[str] = frozenset({"text", "tspan"})

# Default values for SVG attributes that the minifier may drop. Both
# `400` and `normal` are valid defaults for `font-weight`.
_DEFAULT_ATTR_VALUES: dict[str, set[str]] = {
    "font-weight": {"400", "normal"},
}

_XML_DECL_RE = re.compile(r"^\s*<\?xml[^?]*\?>\s*")
_NUMBER_RE = re.compile(r"-?\d+\.\d+")
_HEX_SHORT_RE = re.compile(r"#([0-9A-Fa-f])([0-9A-Fa-f])([0-9A-Fa-f])(?![0-9A-Fa-f])")


def canonicalise(svg: str) -> str:
    """Parse `svg` and return a canonical-form string for comparison.

    Args:
        svg: The SVG markup to canonicalise.

    Returns:
        A canonical-form string. Two SVGs that are visually equivalent
        under the L0 ↔ L1 ↔ L2 lossless contract produce identical
        canonical strings.
    """
    cleaned = _XML_DECL_RE.sub("", svg)
    root = ET.fromstring(cleaned)
    _drop_empty_defs(root)
    _drop_default_attrs(root)
    _normalise_attr_values(root)
    _push_inheriting_attrs_down(root)
    _filter_irrelevant_inherited_attrs(root)
    return _serialise(root)


def assert_dom_equivalent(svg_a: str, svg_b: str, label_a: str = "A", label_b: str = "B") -> None:
    """Assert two SVGs are DOM-equivalent under the visually-lossless contract.

    Args:
        svg_a: First SVG to compare.
        svg_b: Second SVG to compare.
        label_a: Human-readable label for `svg_a` in the failure message.
        label_b: Human-readable label for `svg_b` in the failure message.

    Raises:
        AssertionError: If the two SVGs are not DOM-equivalent. The
            message includes the offset of the first divergence with
            surrounding context for diagnostics.
    """
    canon_a = canonicalise(svg_a)
    canon_b = canonicalise(svg_b)
    if canon_a == canon_b:
        return
    for i, (ca, cb) in enumerate(zip(canon_a, canon_b)):
        if ca != cb:
            start = max(0, i - 40)
            end_a = min(len(canon_a), i + 60)
            end_b = min(len(canon_b), i + 60)
            raise AssertionError(
                f"SVGs not DOM-equivalent (diverge at offset {i}):\n"
                f"  {label_a}: ...{canon_a[start:end_a]!r}...\n"
                f"  {label_b}: ...{canon_b[start:end_b]!r}..."
            )
    raise AssertionError(
        f"SVGs not DOM-equivalent (lengths {len(canon_a)} vs {len(canon_b)}):\n"
        f"  {label_a} tail: ...{canon_a[-60:]!r}\n"
        f"  {label_b} tail: ...{canon_b[-60:]!r}"
    )


def _drop_empty_defs(root: ET.Element) -> None:
    """Remove `<defs>` elements with no children or text (in-place)."""
    for parent in list(root.iter()):
        for child in list(parent):
            if _local(child.tag) == "defs" and len(child) == 0 and not (child.text and child.text.strip()):
                parent.remove(child)


def _drop_default_attrs(root: ET.Element) -> None:
    """Remove attributes carrying default values (in-place)."""
    for elem in root.iter():
        for attr in list(elem.attrib):
            local = _local(attr)
            if local in _DEFAULT_ATTR_VALUES and elem.attrib[attr] in _DEFAULT_ATTR_VALUES[local]:
                del elem.attrib[attr]


def _normalise_attr_values(root: ET.Element) -> None:
    """Expand short hex colours and round decimal numbers to 1dp (in-place)."""
    for elem in root.iter():
        for attr, value in list(elem.attrib.items()):
            value = _HEX_SHORT_RE.sub(lambda m: f"#{m[1]}{m[1]}{m[2]}{m[2]}{m[3]}{m[3]}", value)
            value = _NUMBER_RE.sub(_round_1dp, value)
            elem.set(attr, value)


def _round_1dp(match: re.Match[str]) -> str:
    """Round a matched decimal number to 1dp; strip trailing zeros / dangling dot."""
    rounded = round(float(match.group(0)), 1)
    formatted = f"{rounded:.1f}"
    return formatted.rstrip("0").rstrip(".")


def _push_inheriting_attrs_down(root: ET.Element, inherited: dict[str, str] | None = None) -> None:
    """Push inheriting presentation attributes from ancestors down to leaves (in-place).

    Walks the tree; at each non-leaf, strips inheriting attrs (they're
    pushed); at each leaf, writes the effective inherited+own set.
    Own attributes override inherited ones at every level.
    """
    inherited = dict(inherited or {})
    own: dict[str, str] = {}
    for attr in list(root.attrib):
        local = _local(attr)
        if local in _INHERITING_ATTRS:
            own[local] = root.attrib[attr]
            del root.attrib[attr]
    effective = {**inherited, **own}
    if len(root) == 0:
        for local, value in effective.items():
            root.set(local, value)
    else:
        for child in root:
            _push_inheriting_attrs_down(child, effective)


def _filter_irrelevant_inherited_attrs(root: ET.Element) -> None:
    """Drop text-only inheriting attrs from non-text-rendering elements (in-place).

    After `_push_inheriting_attrs_down`, a hoisted `font-family` lands
    on every leaf — including `<path>` / `<circle>` / `<rect>` that
    don't render text. Strip the spurious attributes so canonical
    forms match across the hoist transform.
    """
    for elem in root.iter():
        if _local(elem.tag) in _TEXT_RENDERING_TAGS:
            continue
        for attr in list(elem.attrib):
            if _local(attr) in _TEXT_ONLY_INHERITING_ATTRS:
                del elem.attrib[attr]


def _serialise(elem: ET.Element) -> str:
    """Serialise an element tree canonically: sorted attrs, no whitespace, no xmlns:* decls."""
    parts: list[str] = []
    _serialise_into(elem, parts)
    return "".join(parts)


def _serialise_into(elem: ET.Element, parts: list[str]) -> None:
    tag = _local(elem.tag)
    parts.append(f"<{tag}")
    bare_attrs = {_local(k): v for k, v in elem.attrib.items() if not k.startswith("xmlns")}
    for key in sorted(bare_attrs):
        parts.append(f' {key}="{bare_attrs[key]}"')
    text = (elem.text or "").strip()
    if len(elem) == 0 and not text:
        parts.append("/>")
        return
    parts.append(">")
    if text:
        parts.append(re.sub(r"\s+", " ", text))
    for child in elem:
        _serialise_into(child, parts)
    parts.append(f"</{tag}>")


def _local(name: str) -> str:
    """Return the local name of a possibly-namespaced tag or attribute."""
    return name.rsplit("}", 1)[-1] if "}" in name else name
