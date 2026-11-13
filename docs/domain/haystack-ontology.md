# Project Haystack Domain Knowledge

## Main Concepts

- Site: A site-level entity.
- Building: A physical building, represented using appropriate
  Haystack tags and relationships.
- Equipment: An asset represented using the equip marker.
- AHU: Equipment identified by the ahu marker.
- Point: A measurement or control point.
- Sensor: A semantic marker identifying sensor points.
- Temp: Temperature semantic marker.
- Air: Air-related semantic marker.

## Tag Categories

### Marker Tags
Examples:
- site
- equip
- ahu
- point
- temp
- sensor
- air

A marker tag is typically represented as m:.

### Value Tags
Examples:
- dis
- unit
- geoCity

These carry values rather than merely indicating tag presence.

### Reference Tags
Examples:
- siteRef
- equipRef

References connect entities.

## Important Rules

1. A marker tag is not a sensor type.
2. A reference does not automatically establish a more specific
   physical or functional relationship.
3. Unresolved references must be reported.
4. Missing relationships must not be invented.
5. The actual Haystack data model and version must be validated
   before implementing production parsing rules.

This document is an initial domain note, not a complete
Project Haystack specification.
