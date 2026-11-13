# Smart Building AI

A locally hosted, domain-specific AI platform for understanding,
analysing and interacting with smart building infrastructure.

## Vision

Build an AI platform that understands:

- Project Haystack ontology
- Building and equipment relationships
- HVAC and BMS systems
- IoT telemetry
- Alarm and fault intelligence
- CAFM/CMMS workflows
- Building operational analytics

## Development Strategy

### Stage 1: Smart Building AI Platform
Build an application using an existing LLM, retrieval,
structured building context and controlled tool execution.

### Stage 2: Smart Building Foundation Model
Develop curated domain datasets, benchmark models and
eventually fine-tune a suitable open-source model.

## Current Environment

- Windows
- 16 GB RAM
- NVIDIA RTX 4050 Laptop GPU (6 GB VRAM)
- Ollama
- Qwen 3.5 4B

## Proposed Technology Stack

| Component | Technology |
|---|---|
| LLM | Qwen / Ollama |
| Backend | Fastify / Node.js |
| Frontend | React |
| Ontology | Project Haystack |
| Database | PostgreSQL |
| Telemetry | TimescaleDB |
| Vector Search | pgvector |
| AI Orchestration | Custom tool orchestration |
| Development | Windows |

## Architecture Principles

1. Building data remains the source of truth.
2. Ontology parsing and relationship resolution are deterministic.
3. LLMs handle reasoning and natural language.
4. Database access goes through controlled backend tools.
5. Dynamic building facts are retrieved, not memorised through fine-tuning.
6. Tenant isolation and permissions are enforced outside the LLM.

## Current Milestones

- [x] Install Ollama
- [x] Install Qwen 3.5 4B
- [x] Verify local inference API
- [x] Test basic smart building reasoning
- [x] Test basic Haystack interpretation
- [ ] Validate missing and invalid references
- [ ] Implement deterministic ontology engine
- [ ] Build synthetic smart building
- [ ] Integrate Qwen with ontology engine
- [ ] Implement telemetry intelligence
- [ ] Implement alarm intelligence
- [ ] Develop model evaluation dataset
- [ ] Fine-tune a domain-specific model

## Getting Started

Install Ollama:
https://ollama.com/download/windows

Pull the model:

```powershell
ollama pull qwen3.5:4b
```

Run:

```powershell
ollama run qwen3.5:4b
```

Local API:

`http://localhost:11434`

## Project Status

Early development / Proof of Concept.

No production building integrations are implemented yet.
