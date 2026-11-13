from typing import Any


MARKER_VALUE = "m:"


def classify_tag(tag: str, value: Any) -> str:
    """
    Classify a Haystack-style tag into:
    - marker: Boolean marker tags such as equip, point, site
    - reference: Reference tags such as siteRef, equipRef
    - value: Tags containing actual values such as dis, unit, geoCity
    """

    if tag.endswith("Ref"):
        return "reference"

    if value == MARKER_VALUE or value is True:
        return "marker"

    return "value"


def classify_record(record: dict) -> dict:
    """
    Classify all tags in a record.

    The entity identifier is metadata and is not classified as a tag.
    """

    result = {
        "marker_tags": [],
        "reference_tags": {},
        "value_tags": {},
    }

    for tag, value in record.items():

        if tag == "id":
            continue

        tag_type = classify_tag(tag, value)

        if tag_type == "marker":
            result["marker_tags"].append(tag)

        elif tag_type == "reference":
            result["reference_tags"][tag] = value

        else:
            result["value_tags"][tag] = value

    return result
