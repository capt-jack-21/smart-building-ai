from src.reference_resolver import resolve_references


def test_valid_site_reference():
    records = [
        {"id": "site-001", "site": "m:"},
        {"id": "equip-001", "equip": "m:", "siteRef": "site-001"}
    ]

    result = resolve_references(records)

    assert len(result["resolved"]) == 1
    assert result["resolved"][0]["target_id"] == "site-001"
    assert result["unresolved"] == []


def test_valid_equipment_reference():
    records = [
        {"id": "equip-001", "equip": "m:", "ahu": "m:"},
        {"id": "point-001", "point": "m:", "equipRef": "equip-001"}
    ]

    result = resolve_references(records)

    assert len(result["resolved"]) == 1
    assert result["resolved"][0]["source_id"] == "point-001"


def test_missing_reference():
    records = [
        {"id": "point-001", "point": "m:", "equipRef": "equip-999"}
    ]

    result = resolve_references(records)

    assert len(result["unresolved"]) == 1
    assert result["unresolved"][0]["reason"] == "target_not_found"


def test_duplicate_entity_ids():
    records = [
        {"id": "equip-001", "equip": "m:"},
        {"id": "equip-001", "equip": "m:"},
        {"id": "point-001", "point": "m:", "equipRef": "equip-001"}
    ]

    result = resolve_references(records)

    assert "equip-001" in result["duplicate_ids"]
    assert result["unresolved"][0]["reason"] == "ambiguous_duplicate_target_id"


def test_invalid_reference_value():
    records = [
        {"id": "point-001", "point": "m:", "equipRef": None}
    ]

    result = resolve_references(records)

    assert len(result["unresolved"]) == 1
    assert result["unresolved"][0]["reason"] == "invalid_reference_value"


def test_missing_entity_id():
    records = [
        {"site": "m:"},
        {"id": "equip-001", "equip": "m:"}
    ]

    result = resolve_references(records)

    assert len(result["invalid_records"]) == 1
