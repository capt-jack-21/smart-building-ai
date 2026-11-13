# Experiment 3 - Reference Validation

## Status: Prepared, awaiting execution and evaluation

## Objective

Evaluate Qwen's handling of:

1. Marker tags
2. Value tags
3. Reference tags
4. Resolved references
5. Missing references
6. Invalid references

## Test Scenarios

- Site entity
- AHU referencing the site
- Temperature point referencing the AHU
- Point without equipment reference
- Point referencing a nonexistent equipment entity

## Expected Behaviour

The model should distinguish tag categories, resolve only
references that exist in the supplied records and report
missing or invalid relationships.

It must not invent relationships.

## Next Step

Execute the experiment through the Ollama /api/chat endpoint
and record the actual response and performance metrics.
