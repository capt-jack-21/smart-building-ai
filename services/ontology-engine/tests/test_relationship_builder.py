from src.relationship_builder import build_relationships


def test_build_site_equipment_point_graph():
    records = [
        {"id": "site-001", "site": "m:", "dis": "London Office"},
        {"id": "equip-001", "equip": "m:", "ahu": "m:", "dis": "AHU-01", "siteRef": "site-001"},
        {"id": "point-001", "point": "m:", "temp": "m:", "dis": "Supply Air Temperature", "unit": "°C", "equipRef": "equip-001"}
    ]

    graph = build_relationships(records)

    assert len(graph["nodes"]) == 3
    assert len(graph["edges"]) == 2

    assert {
        "source": "equip-001",
        "predicate": "siteRef",
        "target": "site-001"
    } in graph["edges"]

    assert {
        "source": "point-001",
        "predicate": "equipRef",
        "target": "equip-001"
    } in graph["edges"]


def test_missing_reference_does_not_create_edge():
    records = [
        {"id": "point-001", "point": "m:", "equipRef": "equip-999"}
    ]

    graph = build_relationships(records)

    assert graph["edges"] == []
    assert len(graph["diagnostics"]["unresolved"]) == 1


def test_preserve_original_reference_predicate():
    records = [
        {"id": "site-001", "site": "m:"},
        {"id": "equip-001", "equip": "m:", "siteRef": "site-001"}
    ]

    graph = build_relationships(records)

    assert graph["edges"][0]["predicate"] == "siteRef"


def test_duplicate_entities_are_not_added_as_nodes():
    records = [
        {"id": "equip-001", "equip": "m:"},
        {"id": "equip-001", "equip": "m:"}
    ]

    graph = build_relationships(records)

    assert graph["nodes"] == []
    assert "equip-001" in graph["diagnostics"]["duplicate_ids"]


def test_invalid_record_is_not_added_as_node():
    records = [
        {"site": "m:"},
        {"id": "site-001", "site": "m:"}
    ]

    graph = build_relationships(records)

    assert len(graph["nodes"]) == 1
    assert len(graph["diagnostics"]["invalid_records"]) == 1
