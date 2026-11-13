from typing import Any


def resolve_references(records: list[dict[str, Any]]) -> dict:
    """
    Resolve reference tags against entity IDs.

    Reference convention for this initial implementation:
    Any tag ending in 'Ref' is treated as a reference.
    """

    entity_index = {}
    duplicate_ids = []
    invalid_records = []

    # 1. Build entity index
    for record in records:
        entity_id = record.get("id")

        if not isinstance(entity_id, str) or not entity_id:
            invalid_records.append(record)
            continue

        if entity_id in entity_index:
            if entity_id not in duplicate_ids:
                duplicate_ids.append(entity_id)
        else:
            entity_index[entity_id] = record

    resolved = []
    unresolved = []

    # 2. Resolve references
    for record in records:
        source_id = record.get("id")

        if not isinstance(source_id, str) or not source_id:
            continue

        for tag, target_id in record.items():

            if not tag.endswith("Ref"):
                continue

            if not isinstance(target_id, str) or not target_id:
                unresolved.append({
                    "source_id": source_id,
                    "reference_tag": tag,
                    "target_id": target_id,
                    "reason": "invalid_reference_value"
                })
                continue

            if target_id in duplicate_ids:
                unresolved.append({
                    "source_id": source_id,
                    "reference_tag": tag,
                    "target_id": target_id,
                    "reason": "ambiguous_duplicate_target_id"
                })
                continue

            if target_id not in entity_index:
                unresolved.append({
                    "source_id": source_id,
                    "reference_tag": tag,
                    "target_id": target_id,
                    "reason": "target_not_found"
                })
                continue

            resolved.append({
                "source_id": source_id,
                "reference_tag": tag,
                "target_id": target_id
            })

    return {
        "resolved": resolved,
        "unresolved": unresolved,
        "duplicate_ids": duplicate_ids,
        "invalid_records": invalid_records
    }
