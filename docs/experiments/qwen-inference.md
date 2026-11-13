# Experiment 1 - Qwen Local Inference

## Environment

- Model: qwen3.5:4b
- Runtime: Ollama
- Hardware: NVIDIA RTX 4050 Laptop GPU
- VRAM: 6 GB

## Objective

Test Qwen's ability to explain relationships between:

- Site
- Building
- HVAC system
- AHU
- Supply air temperature sensor

## Result

Qwen returned structured JSON containing a conceptual hierarchy,
functional relationships and a data flow sequence.

## Observation

The model understands general smart building terminology.

However, its generated hierarchy should not be treated as a
valid Project Haystack entity model without verification.

## Conclusion

Basic domain reasoning works locally.
Further ontology-specific evaluation is required.
