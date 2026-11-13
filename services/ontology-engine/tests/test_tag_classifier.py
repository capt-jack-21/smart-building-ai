from src.tag_classifier import classify_tag, classify_record


def test_marker_tag():
    assert classify_tag("equip", "m:") == "marker"


def test_boolean_marker_tag():
    assert classify_tag("site", True) == "marker"


def test_reference_tag():
    assert classify_tag("equipRef", "equip-001") == "reference"


def test_value_tag():
    assert classify_tag("unit", "°C") == "value"


def test_record_classification():
    record = {
        "id": "point-001",
        "point": "m:",
        "temp": "m:",
        "sensor": "m:",
        "dis": "Supply Air Temperature",
        "unit": "°C",
        "equipRef": "equip-001",
    }

    result = classify_record(record)

    assert set(result["marker_tags"]) == {
        "point", "temp", "sensor"
    }

    assert result["reference_tags"] == {
        "equipRef": "equip-001"
    }

    assert result["value_tags"] == {
        "dis": "Supply Air Temperature",
        "unit": "°C",
    }
