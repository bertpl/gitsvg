"""CSS class extraction step — hierarchical shared-trunk-then-exact-match algorithm.

Detects repeated presentation-attribute clusters across rendered SVG
elements and hoists them into a `<style>` block at the top, replacing
inline attributes with `class="cN"` (or multi-class `class="cN cM"`)
references. Enabled at L2+.

Two passes:

1. **Trunk pass.** For each tag-kind (all `<path>`, all `<text>`, …)
   with at least two elements, compute the trunk = intersection of
   every member's presentation cluster. When non-empty, emit it as a
   class shared by every member of the tag-kind. Catches the common
   "shared structural baseline plus varying color" pattern (e.g. all
   branch lines share `stroke-width` / `fill` but vary in `stroke`).

2. **Leaf pass.** After trunk removal, run exact-match clustering on
   the residual clusters across all elements. Clusters with at least
   two members become additional classes; affected elements gain a
   second class entry.

Trunk and leaf attribute sets are disjoint by construction (the leaf
pass operates on residuals, which exclude trunk attributes), so
multi-class assignments like `class="c1 c3"` carry no CSS-specificity
risk — declaration order in the `<style>` block doesn't affect
rendering.

Class names are `c1`, `c2`, … assigned in deterministic extraction
order (trunks by tag-kind alphabetical, then leaves by first-seen).
"""

import itertools
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from collections.abc import Iterator

from defusedxml.ElementTree import fromstring as _defused_fromstring

_SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", _SVG_NS)

# Attributes whose values are interpreted as CSS `<length>` and therefore
# require a unit suffix when expressed in CSS (i.e. inside a `<style>`
# block). SVG presentation-attribute form accepts bare numerics, but the
# CSS parser rejects them and falls back to the default — leaving text
# rendered at the browser default size, for example.
_CSS_LENGTH_ATTRS: frozenset[str] = frozenset({"font-size"})

# Presentation attributes that are valid CSS properties and thus
# eligible for class extraction. Geometry attributes (x, y, cx, cy, r,
# width, height, d, transform) and structural attributes (id, href,
# class) are not eligible.
_PRESENTATION_ATTRS: frozenset[str] = frozenset(
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
        "opacity",
        "color",
    }
)

_XML_DECL_RE = re.compile(r"^\s*<\?xml[^?]*\?>\s*")


def extract_css_classes(svg: str) -> str:
    """Extract repeated presentation-attribute clusters into a `<style>` block.

    Args:
        svg: The full SVG markup as a string. Numeric and hex values
            should already be normalized (rounding and hex shortening
            run before extraction so the style block carries the same
            normalized forms as any leftover inline attributes).

    Returns:
        The SVG with eligible attribute clusters hoisted into a
        `<style>` block prepended as the first child of `<svg>`. When
        no cluster meets the extraction threshold, returns the input
        unchanged.
    """
    decl_match = _XML_DECL_RE.match(svg)
    xml_decl = decl_match.group(0) if decl_match else ""
    body = svg[len(xml_decl) :]

    try:
        root = _defused_fromstring(body)
    except ET.ParseError:
        return svg

    elem_classes: defaultdict[int, list[str]] = defaultdict(list)
    counter = itertools.count(1)
    # Trunk before leaf: the leaf pass clusters the *residual* attributes that
    # the trunk pass leaves behind, so it must read an already-stripped tree.
    class_defs = _trunk_pass(root, counter, elem_classes)
    class_defs += _leaf_pass(root, counter, elem_classes)

    if not class_defs:
        return svg

    # --- write class attribute + style block ---
    for elem in root.iter():
        classes = elem_classes.get(id(elem))
        if classes:
            elem.set("class", " ".join(classes))

    style_text = _format_style_block(class_defs)
    style_elem = ET.Element(_qualified("style", root))
    style_elem.text = style_text
    root.insert(0, style_elem)

    return xml_decl + ET.tostring(root, encoding="unicode")


def _trunk_pass(
    root: ET.Element,
    counter: Iterator[int],
    elem_classes: defaultdict[int, list[str]],
) -> list[tuple[str, dict[str, str]]]:
    """Per tag-kind, extract the attribute intersection shared by all members.

    Groups elements (with a non-empty cluster) by tag, and for each group of
    two or more emits the non-empty intersection of their clusters as one
    shared class. Strips the trunk attributes inline and records the class on
    each member via `elem_classes`.

    Returns:
        The `(class_name, cluster)` definitions emitted, in tag-alphabetical
        order.
    """
    groups = _group_by_tag(root)
    defs: list[tuple[str, dict[str, str]]] = []
    for tag in sorted(groups):
        elems = groups[tag]
        trunk = _intersect_clusters([_cluster(e) for e in elems])
        emitted = _emit_class(elems, trunk, counter, elem_classes)
        if emitted is not None:
            defs.append(emitted)
    return defs


def _leaf_pass(
    root: ET.Element,
    counter: Iterator[int],
    elem_classes: defaultdict[int, list[str]],
) -> list[tuple[str, dict[str, str]]]:
    """Exact-match clustering of the residual attributes left after trunk removal.

    Groups elements by their (now-residual) cluster, and for each group of two
    or more emits that cluster as one shared class. Strips it inline and records
    the class on each member via `elem_classes`.

    Returns:
        The `(class_name, cluster)` definitions emitted, in first-seen order.
    """
    groups, order = _group_by_residual(root)
    defs: list[tuple[str, dict[str, str]]] = []
    for key in order:
        emitted = _emit_class(groups[key], dict(key), counter, elem_classes)
        if emitted is not None:
            defs.append(emitted)
    return defs


def _group_by_tag(root: ET.Element) -> defaultdict[str, list[ET.Element]]:
    """Group elements with a non-empty presentation cluster by local tag name."""
    groups: defaultdict[str, list[ET.Element]] = defaultdict(list)
    for elem in root.iter():
        if _cluster(elem):
            groups[_local(elem.tag)].append(elem)
    return groups


def _group_by_residual(
    root: ET.Element,
) -> tuple[dict[tuple[tuple[str, str], ...], list[ET.Element]], list[tuple[tuple[str, str], ...]]]:
    """Group elements by their residual cluster (sorted-items key), keeping first-seen order.

    Returns:
        `(groups, order)` — the cluster-key → elements map and the keys in the
        order they were first encountered (so class numbering is deterministic).
    """
    groups: dict[tuple[tuple[str, str], ...], list[ET.Element]] = {}
    order: list[tuple[tuple[str, str], ...]] = []
    for elem in root.iter():
        residual = _cluster(elem)
        if not residual:
            continue
        key = tuple(sorted(residual.items()))
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(elem)
    return groups, order


def _emit_class(
    elems: list[ET.Element],
    cluster: dict[str, str],
    counter: Iterator[int],
    elem_classes: defaultdict[int, list[str]],
) -> tuple[str, dict[str, str]] | None:
    """Emit one shared class for `cluster` across `elems`, stripping it inline.

    The shared "threshold → name → strip → record" tail of both passes.

    Args:
        elems: The elements that share `cluster`.
        cluster: The attribute (name → value) set to hoist into a class.
        counter: Source of sequential class numbers.
        elem_classes: Per-element class list, appended to in place.

    Returns:
        The `(class_name, cluster-copy)` definition, or `None` when the group
        has fewer than two members or `cluster` is empty (no class assigned).
    """
    if len(elems) < 2 or not cluster:
        return None
    class_name = _next_class(counter)
    for elem in elems:
        for attr in cluster:
            if attr in elem.attrib:
                del elem.attrib[attr]
        elem_classes[id(elem)].append(class_name)
    return class_name, dict(cluster)


def _next_class(counter: Iterator[int]) -> str:
    """Return the next sequential class name (`c1`, `c2`, ...)."""
    return f"c{next(counter)}"


def _cluster(elem: ET.Element) -> dict[str, str]:
    """Return the eligible presentation cluster of `elem` (attribute name → value)."""
    return {_local(k): v for k, v in elem.attrib.items() if _local(k) in _PRESENTATION_ATTRS}


def _intersect_clusters(clusters: list[dict[str, str]]) -> dict[str, str]:
    """Return the (attribute, value) pairs common to every cluster."""
    if not clusters:
        return {}
    common_attrs = set(clusters[0].keys())
    for c in clusters[1:]:
        common_attrs &= c.keys()
    return {attr: clusters[0][attr] for attr in common_attrs if all(c[attr] == clusters[0][attr] for c in clusters)}


def _format_style_block(class_defs: list[tuple[str, dict[str, str]]]) -> str:
    """Format the class definitions as a compact CSS string."""
    parts = []
    for name, cluster in class_defs:
        decls = ";".join(f"{a}:{_css_value(a, v)}" for a, v in sorted(cluster.items()))
        parts.append(f".{name}{{{decls}}}")
    return "".join(parts)


def _css_value(attr: str, value: str) -> str:
    """Format `value` for CSS-property context, adding `px` where the spec requires a unit.

    SVG presentation attributes accept bare numerics (`font-size="11"`);
    CSS does not (`font-size: 11` is invalid and falls back to default).
    Append `px` to bare numerics for attributes listed in
    `_CSS_LENGTH_ATTRS`. Other SVG-specific length properties like
    `stroke-width` are unitless in SVG CSS without browser quirks.
    """
    if attr in _CSS_LENGTH_ATTRS and _is_bare_number(value):
        return f"{value}px"
    return value


def _is_bare_number(value: str) -> bool:
    """Whether `value` parses as a plain numeric string with no unit suffix."""
    try:
        float(value)
        return True
    except ValueError:
        return False


def _local(name: str) -> str:
    """Return the local name of a possibly-namespaced tag or attribute."""
    return name.rsplit("}", 1)[-1] if "}" in name else name


def _qualified(local_name: str, root: ET.Element) -> str:
    """Return `local_name` qualified with the SVG namespace iff the root is namespaced."""
    if root.tag.startswith(f"{{{_SVG_NS}}}"):
        return f"{{{_SVG_NS}}}{local_name}"
    return local_name
