"""Deterministic Haystack Ontology Intelligence Engine (v0.1).

Parses Haystack-style records, classifies tags, identifies entities, resolves
references, detects problems and builds a validated site -> equip -> point
hierarchy.  The LLM never decides any of this; it only receives the result.

Relationship semantics are deliberately NOT invented: a resolved `equipRef`
is reported as the tag it is ("equipRef: point-001 -> equip-001"), never as
"measures_via" or similar.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from .tags import MARKER, REF, VALUE, Tag, classify_tag, is_ref_name, normalize_id

DEFAULT_ENTITY_KINDS = ("site", "space", "equip", "point")
POINT_FUNCTIONS = ("sensor", "cmd", "sp")

# Which entity kind a given ref tag must point at. Unlisted *Ref tags are only
# checked for existence.
REF_TARGET_KINDS: dict[str, tuple[str, ...]] = {
    "siteRef": ("site",),
    "spaceRef": ("space",),
    "floorRef": ("space",),
    "equipRef": ("equip",),
    "ahuRef": ("equip",),
    "vavRef": ("equip",),
    "systemRef": ("equip",),
}

ERROR, WARNING = "error", "warning"


@dataclass
class Entity:
    id: str
    dis: str | None
    kind: str | None                      # site/space/equip/point or None if unclassifiable
    tags: dict[str, Tag]
    position: int                         # index in the input

    @property
    def markers(self) -> list[str]:
        return sorted(t.name for t in self.tags.values() if t.kind == MARKER)

    @property
    def value_tags(self) -> list[str]:
        return sorted(t.name for t in self.tags.values() if t.kind == VALUE)

    @property
    def ref_tags(self) -> list[str]:
        return sorted(t.name for t in self.tags.values() if t.kind == REF)


@dataclass
class Relationship:
    source: str
    tag: str
    target: str | None
    status: str                           # resolved | unresolved | wrong_kind
    target_kind: str | None = None


@dataclass
class Issue:
    code: str
    severity: str
    entity: str
    message: str
    tag: str | None = None


@dataclass
class OntologyGraph:
    entities: dict[str, Entity] = field(default_factory=dict)
    relationships: list[Relationship] = field(default_factory=list)
    issues: list[Issue] = field(default_factory=list)
    site_of: dict[str, str | None] = field(default_factory=dict)       # derived
    parent_equip: dict[str, str | None] = field(default_factory=dict)  # derived
    equip_of: dict[str, str | None] = field(default_factory=dict)      # points, derived
    hierarchy: dict[str, Any] = field(default_factory=dict)

    # ---- queries (used later as LLM tools) --------------------------------
    def get(self, entity_id: str) -> Entity | None:
        return self.entities.get(entity_id)

    def with_marker(self, marker: str, kind: str | None = None) -> list[Entity]:
        return [e for e in self.entities.values()
                if marker in e.tags and e.tags[marker].kind == MARKER and (kind is None or e.kind == kind)]

    def equips_of_site(self, site_id: str) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "equip" and self.site_of.get(e.id) == site_id]

    def points_of_equip(self, equip_id: str) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "point" and self.equip_of.get(e.id) == equip_id]

    def issues_for(self, entity_id: str) -> list[Issue]:
        return [i for i in self.issues if i.entity == entity_id]

    @property
    def ok(self) -> bool:
        return not any(i.severity == ERROR for i in self.issues)

    # ---- serialisation ------------------------------------------------------
    def to_dict(self) -> dict[str, Any]:
        kinds: dict[str, int] = {}
        for e in self.entities.values():
            kinds[e.kind or "unclassified"] = kinds.get(e.kind or "unclassified", 0) + 1
        return {
            "summary": {
                "entities": len(self.entities),
                "by_kind": kinds,
                "relationships": len(self.relationships),
                "unresolved_refs": sum(r.status != "resolved" for r in self.relationships),
                "errors": sum(i.severity == ERROR for i in self.issues),
                "warnings": sum(i.severity == WARNING for i in self.issues),
                "valid": self.ok,
            },
            "entities": [self._entity_dict(e) for e in self.entities.values()],
            "relationships": [r.__dict__ for r in self.relationships],
            "hierarchy": self.hierarchy,
            "issues": [i.__dict__ for i in self.issues],
        }

    def _entity_dict(self, e: Entity) -> dict[str, Any]:
        rels = {r.tag: r for r in self.relationships if r.source == e.id}
        return {
            "id": e.id,
            "dis": e.dis,
            "kind": e.kind,
            "markers": e.markers,
            "values": {t.name: t.value for t in e.tags.values() if t.kind == VALUE},
            "refs": {n: {"target": rels[n].target, "status": rels[n].status} for n in e.ref_tags if n in rels},
            "derived": {"site": self.site_of.get(e.id), "equip": self.equip_of.get(e.id),
                        "parent_equip": self.parent_equip.get(e.id)},
        }

    def to_eval_schema(self) -> dict[str, Any]:
        """Ground truth in the exact shape Experiment 3 asks the LLM to produce."""
        entities = [{"id": e.id, "kind": e.kind, "marker_tags": e.markers,
                     "value_tags": e.value_tags, "ref_tags": e.ref_tags}
                    for e in self.entities.values()]
        rels = [{"from": r.source, "tag": r.tag, "to": r.target, "status": r.status}
                for r in self.relationships]
        missing = [{"entity": i.entity, "expected_tag": i.tag}
                   for i in self.issues if i.code == "MISSING_EXPECTED_REF"]
        return {"entities": entities, "relationships": rels, "missing_relationships": missing}


def _rows(data: Any) -> list[Any]:
    if isinstance(data, dict) and isinstance(data.get("rows"), list):   # Haystack JSON grid
        return data["rows"]
    if isinstance(data, list):
        return data
    raise TypeError("Expected a list of records or a Haystack grid with 'rows'")


def analyze(data: Any, entity_kinds: Iterable[str] = DEFAULT_ENTITY_KINDS,
            truthy_markers: bool = False) -> OntologyGraph:
    """Parse, classify, resolve and validate Haystack records."""
    entity_kinds = tuple(entity_kinds)
    g = OntologyGraph()
    issue = lambda code, sev, ent, msg, tag=None: g.issues.append(Issue(code, sev, ent, msg, tag))

    # 1. parse records into entities ------------------------------------------------
    for pos, rec in enumerate(_rows(data)):
        if not isinstance(rec, dict):
            issue("INVALID_RECORD", ERROR, f"#{pos}", f"Record #{pos} is not an object")
            continue
        eid = normalize_id(rec.get("id"))
        if not eid:
            issue("MISSING_ID", ERROR, f"#{pos}", f"Record #{pos} has no usable 'id'")
            continue
        if eid in g.entities:
            issue("DUPLICATE_ID", ERROR, eid, f"Id '{eid}' appears more than once; later record ignored")
            continue

        tags = {k: classify_tag(k, v, truthy_markers) for k, v in rec.items() if k != "id"}
        markers = [k for k in entity_kinds if k in tags and tags[k].kind == MARKER]
        if len(markers) == 1:
            kind = markers[0]
        else:
            kind = None
            if not markers:
                issue("NO_ENTITY_KIND", ERROR, eid,
                      f"None of {list(entity_kinds)} present as a marker; entity cannot be classified")
            else:
                issue("MULTIPLE_ENTITY_KINDS", ERROR, eid, f"Entity has several kind markers: {markers}")

        dis = tags["dis"].value if "dis" in tags and tags["dis"].kind == VALUE else None
        ent = Entity(eid, dis, kind, tags, pos)
        g.entities[eid] = ent

        for name in (*entity_kinds, *POINT_FUNCTIONS):
            if name in tags and tags[name].kind != MARKER:
                issue("KNOWN_MARKER_NOT_MARKER", ERROR, eid,
                      f"'{name}' must be a marker but holds a {tags[name].kind} ({tags[name].raw!r})", name)
        for t in tags.values():
            if is_ref_name(t.name) and t.kind != REF:
                issue("REF_TAG_NOT_REF", ERROR, eid,
                      f"'{t.name}' looks like a reference but holds {t.raw!r}", t.name)

    # 2. resolve references ----------------------------------------------------------
    resolved: dict[tuple[str, str], str] = {}     # (source, tag) -> target id, only when fully valid
    for e in g.entities.values():
        for t in e.tags.values():
            if t.kind != REF:
                continue
            target = normalize_id(t.value)
            if target is None:
                g.relationships.append(Relationship(e.id, t.name, None, "unresolved"))
                issue("UNRESOLVED_REF", ERROR, e.id, f"'{t.name}' has an empty/unparseable target {t.raw!r}", t.name)
                continue
            tgt = g.entities.get(target)
            if tgt is None:
                g.relationships.append(Relationship(e.id, t.name, target, "unresolved"))
                issue("UNRESOLVED_REF", ERROR, e.id, f"'{t.name}' points to '{target}', which does not exist", t.name)
                continue
            expected = REF_TARGET_KINDS.get(t.name)
            if expected and tgt.kind not in expected:
                g.relationships.append(Relationship(e.id, t.name, target, "wrong_kind", tgt.kind))
                issue("REF_WRONG_TARGET_KIND", ERROR, e.id,
                      f"'{t.name}' must point to {list(expected)} but '{target}' is {tgt.kind or 'unclassified'}", t.name)
                continue
            g.relationships.append(Relationship(e.id, t.name, target, "resolved", tgt.kind))
            resolved[(e.id, t.name)] = target

    # 3. equipment parent chain (nested equip via equipRef), cycle-safe -------------------
    equips = [e for e in g.entities.values() if e.kind == "equip"]
    for e in equips:
        g.parent_equip[e.id] = resolved.get((e.id, "equipRef"))
    cyclic: set[str] = set()
    for e in equips:
        seen, cur = [], e.id
        while cur and cur not in seen:
            seen.append(cur)
            cur = g.parent_equip.get(cur)
        if cur and cur in seen:
            cyclic.update(seen[seen.index(cur):])
    for cid in sorted(cyclic):
        g.parent_equip[cid] = None
        issue("EQUIP_REF_CYCLE", ERROR, cid, "Equipment parent chain via equipRef contains a cycle", "equipRef")

    # 4. derive site / equip membership, check consistency ------------------------------
    memo: dict[str, str | None] = {}

    def equip_site(eid: str) -> str | None:
        if eid in memo:
            return memo[eid]
        memo[eid] = None                                    # guard
        own = resolved.get((eid, "siteRef"))
        parent = g.parent_equip.get(eid)
        inherited = equip_site(parent) if parent else None
        if own and inherited and own != inherited:
            issue("SITEREF_MISMATCH", ERROR, eid,
                  f"siteRef '{own}' disagrees with parent equipment's site '{inherited}'", "siteRef")
        memo[eid] = own or inherited
        return memo[eid]

    for e in equips:
        g.site_of[e.id] = equip_site(e.id)
        if "siteRef" not in e.tags and "equipRef" not in e.tags:
            issue("MISSING_EXPECTED_REF", WARNING, e.id, "Equipment has neither siteRef nor equipRef", "siteRef")

    for e in g.entities.values():
        if e.kind == "point":
            eq = resolved.get((e.id, "equipRef"))
            g.equip_of[e.id] = eq
            own_site = resolved.get((e.id, "siteRef"))
            inherited = g.site_of.get(eq) if eq else None
            if own_site and inherited and own_site != inherited:
                issue("SITEREF_MISMATCH", ERROR, e.id,
                      f"siteRef '{own_site}' disagrees with equipment's site '{inherited}'", "siteRef")
            g.site_of[e.id] = own_site or inherited
            if "equipRef" not in e.tags:
                issue("MISSING_EXPECTED_REF", WARNING, e.id,
                      "Point has no equipRef; association with equipment is unknown "
                      "(acceptable only for site-level points)", "equipRef")
            funcs = [f for f in POINT_FUNCTIONS if f in e.tags and e.tags[f].kind == MARKER]
            if len(funcs) != 1:
                issue("POINT_FUNCTION_TAG", WARNING, e.id,
                      f"Point should have exactly one of {list(POINT_FUNCTIONS)}; found {funcs}")
        elif e.kind == "space":
            g.site_of[e.id] = resolved.get((e.id, "siteRef"))

    g.hierarchy = _build_hierarchy(g)
    return g


def _node(e: Entity) -> dict[str, Any]:
    return {"id": e.id, "dis": e.dis, "kind": e.kind}


def _build_hierarchy(g: OntologyGraph) -> dict[str, Any]:
    ents = g.entities
    children: dict[str, list[str]] = {}
    for eid, parent in g.parent_equip.items():
        if parent:
            children.setdefault(parent, []).append(eid)

    def equip_node(eid: str) -> dict[str, Any]:
        n = _node(ents[eid])
        n["points"] = [_node(p) for p in g.points_of_equip(eid)]
        n["children"] = [equip_node(c) for c in children.get(eid, [])]
        return n

    sites = []
    for s in (e for e in ents.values() if e.kind == "site"):
        roots = [e.id for e in g.equips_of_site(s.id) if not g.parent_equip.get(e.id)]
        n = _node(s)
        n["equips"] = [equip_node(r) for r in roots]
        n["site_level_points"] = [_node(p) for p in ents.values()
                                  if p.kind == "point" and not g.equip_of.get(p.id) and g.site_of.get(p.id) == s.id]
        sites.append(n)

    unattached_equips = [e.id for e in ents.values() if e.kind == "equip" and not g.site_of.get(e.id)]
    unattached_points = [e.id for e in ents.values()
                         if e.kind == "point" and not g.equip_of.get(e.id) and not g.site_of.get(e.id)]
    unclassified = [e.id for e in ents.values() if e.kind is None]
    return {"sites": sites,
            "unattached": {"equips": unattached_equips, "points": unattached_points, "unclassified": unclassified}}
