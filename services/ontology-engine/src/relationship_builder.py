from typing import Any

from src.reference_resolver import resolve_references


def build_relationships(records: list[dict[str, Any]]) -> dict:
    """
    Build a graph from entities and successfully resolved references.

    Important:
    - Only resolved references become graph edges.
    - The original reference tag is preserved as the predicate.
    - No semantic relationship is inferred by the LLM or this module.
    """

    resolution = resolve_references(records)

    nodes = []
    seen_ids = set()

    for record in records:
        entity_id = record.get("id")

        if not isinstance(entity_id, str) or not entity_id:
            continue

        if entity_id in seen_ids:
            continue

        if entity_id in resolution["duplicate_ids"]:
            continue

        seen_ids.add(entity_id)

        nodes.append({
            "id": entity_id,
            "dis": record.get("dis")
        })

    edges = [
        {
            "source": reference["source_id"],
            "predicate": reference["reference_tag"],
            "target": reference["target_id"]
        }
        for reference in resolution["resolved"]
    ]

    return {
        "nodes": nodes,
        "edges": edges,
        "diagnostics": {
            "unresolved": resolution["unresolved"],
            "duplicate_ids": resolution["duplicate_ids"],
            "invalid_records": resolution["invalid_records"]
        }
    }
