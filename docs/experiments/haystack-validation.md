# Experiment 2 - Haystack Interpretation

## Objective

Test whether Qwen can interpret synthetic Haystack-style records.

## Input Entities

### Site

- id: site-001
- dis: London Office
- site: m:
- geoCity: London

### Equipment

- id: equip-001
- dis: AHU-01
- equip: m:
- ahu: m:
- siteRef: site-001

### Point

- id: point-001
- dis: AHU-01 Supply Air Temperature
- point: m:
- temp: m:
- sensor: m:
- air: m:
- unit: °C
- equipRef: equip-001

## Observed Results

Qwen correctly identified:

- Site entity
- Equipment entity
- Temperature point
- Semantic marker tags
- equipRef
- siteRef

## Identified Errors

1. Qwen interpreted equipRef as measures_via.
   This relationship meaning was more specific than the supplied
   reference alone justified.

2. Qwen interpreted sensor: m: as a sensor type.
   This is a marker tag, not a sensor type.

## Performance

- Model: qwen3.5:4b
- Prompt tokens: 291
- Generated tokens: 2664
- Generation speed: 54.07 tokens/sec
- Total duration: 49.72 seconds

## Conclusion

Qwen can interpret basic Haystack-style records, but it needs
deterministic validation and more domain-specific evaluation.
