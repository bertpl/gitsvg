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

import re
import xml.etree.ElementTree as ET
from collections import defaultdict

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
        root = ET.fromstring(body)
    except ET.ParseError:
        return svg

    class_defs: list[tuple[str, dict[str, str]]] = []
    elem_classes: defaultdict[int, list[str]] = defaultdict(list)
    next_id = [1]

    def _new_class() -> str:
        """Return the next sequential class name (`c1`, `c2`, ...) and bump the counter."""
        name = f"c{next_id[0]}"
        next_id[0] += 1
        return name

    # --- trunk pass ---------------------
    elements_by_tag: defaultdict[str, list[ET.Element]] = defaultdict(list)
    for elem in root.iter():
        if _cluster(elem):
            elements_by_tag[_local(elem.tag)].append(elem)

    for tag in sorted(elements_by_tag):
        elems = elements_by_tag[tag]
        if len(elems) < 2:
            continue
        clusters = [_cluster(e) for e in elems]
        trunk = _intersect_clusters(clusters)
        if not trunk:
            continue
        class_name = _new_class()
        class_defs.append((class_name, dict(trunk)))
        for elem in elems:
            for attr in trunk:
                del elem.attrib[attr]
            elem_classes[id(elem)].append(class_name)

    # --- leaf pass ----------------------
    leaf_groups: dict[tuple[tuple[str, str], ...], list[ET.Element]] = {}
    leaf_order: list[tuple[tuple[str, str], ...]] = []
    for elem in root.iter():
        residual = _cluster(elem)
        if not residual:
            continue
        key = tuple(sorted(residual.items()))
        if key not in leaf_groups:
            leaf_groups[key] = []
            leaf_order.append(key)
        leaf_groups[key].append(elem)

    for key in leaf_order:
        elems = leaf_groups[key]
        if len(elems) < 2:
            continue
        class_name = _new_class()
        cluster_dict = dict(key)
        class_defs.append((class_name, cluster_dict))
        for elem in elems:
            for attr in cluster_dict:
                if attr in elem.attrib:
                    del elem.attrib[attr]
            elem_classes[id(elem)].append(class_name)

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
