"""Tag classification: marker / reference / value.

Handles the encodings seen in practice:
  * Haystack JSON v3 string prefixes: "m:" marker, "r:id Display" ref, "n:72 degF" number, "s:text" ...
  * Haystack JSON v4 objects: {"_kind": "marker"}, {"_kind": "ref", "val": "..."} ...
  * Plain strings used by simplified exports: "siteRef": "site-001"  (ref, by naming convention)

Nothing here calls an LLM. Same input -> same output.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

MARKER = "marker"
REF = "ref"
VALUE = "value"

_REF_NAME = re.compile(r"^[a-z][A-Za-z0-9_]*Ref$")
_NUMBER = re.compile(r"^n:\s*(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*(.*)$")
_PREFIX_TYPES = {"s": "string", "d": "date", "h": "time", "t": "datetime", "u": "uri"}


@dataclass(frozen=True)
class Tag:
    name: str
    kind: str                 # MARKER | REF | VALUE
    value_type: str | None    # for VALUE: number/string/bool/null/...; for REF: "ref"
    value: Any                # normalised value (refs keep the raw target text)
    raw: Any                  # exactly what was in the record


def is_ref_name(name: str) -> bool:
    """Haystack convention: tag names ending in 'Ref' are references."""
    return bool(_REF_NAME.match(name))


def classify_tag(name: str, raw: Any, truthy_markers: bool = False) -> Tag:
    """Classify one tag. `truthy_markers=True` treats JSON `true` as a marker."""
    if isinstance(raw, dict):
        k = raw.get("_kind")
        if k == "marker":
            return Tag(name, MARKER, None, True, raw)
        if k == "ref":
            return Tag(name, REF, "ref", raw.get("val"), raw)
        if k == "number":
            return Tag(name, VALUE, "number", {"value": raw.get("val"), "unit": raw.get("unit")}, raw)
        return Tag(name, VALUE, k or "dict", raw, raw)

    if isinstance(raw, bool):
        if raw and truthy_markers:
            return Tag(name, MARKER, None, True, raw)
        return Tag(name, VALUE, "bool", raw, raw)
    if isinstance(raw, (int, float)):
        return Tag(name, VALUE, "number", {"value": raw, "unit": None}, raw)
    if raw is None:
        return Tag(name, VALUE, "null", None, raw)
    if isinstance(raw, list):
        return Tag(name, VALUE, "list", raw, raw)

    if isinstance(raw, str):
        if raw == "m:":
            return Tag(name, MARKER, None, True, raw)
        if raw.startswith("r:"):
            return Tag(name, REF, "ref", raw[2:], raw)
        if raw == "z:":
            return Tag(name, VALUE, "null", None, raw)
        m = _NUMBER.match(raw)
        if m:
            return Tag(name, VALUE, "number", {"value": float(m.group(1)), "unit": m.group(2) or None}, raw)
        if len(raw) >= 2 and raw[1] == ":" and raw[0] in _PREFIX_TYPES:
            return Tag(name, VALUE, _PREFIX_TYPES[raw[0]], raw[2:], raw)
        if is_ref_name(name):
            return Tag(name, REF, "ref", raw, raw)
        return Tag(name, VALUE, "string", raw, raw)

    return Tag(name, VALUE, type(raw).__name__, raw, raw)


def normalize_id(v: Any) -> str | None:
    """'r:equip-001 AHU-01' / '@equip-001' / 'equip-001' -> 'equip-001'."""
    if isinstance(v, dict):
        v = v.get("val")
    if not isinstance(v, str):
        return None
    s = v.strip()
    if s.startswith("r:"):
        s = s[2:]
    if s.startswith("@"):
        s = s[1:]
    parts = s.split(None, 1)
    return parts[0] if parts else None
