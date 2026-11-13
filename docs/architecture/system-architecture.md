# System Architecture

## Overview

Smart Building AI is designed as a modular intelligence platform.

## Logical Components

1. React user interface
2. Fastify API and AI orchestrator
3. Qwen inference through Ollama
4. Retrieval and knowledge engine
5. Deterministic ontology engine
6. Building tool gateway
7. TimescaleDB telemetry access
8. External BMS and CAFM/CMMS integrations

## Core Flow

User Question
    |
    v
Fastify AI Orchestrator
    |
    +---- Qwen LLM
    |
    +---- Knowledge Retrieval
    |
    v
Smart Building Tool Gateway
    |
    +---- Ontology Engine
    +---- TimescaleDB
    +---- BMS APIs
    +---- CAFM/CMMS APIs
    |
    v
Validated Context
    |
    v
LLM Response

## Architectural Principle

The LLM must not be the source of truth for building entities,
relationships, telemetry or permissions.

Backend services resolve and validate these facts.
The LLM interprets and explains them.
