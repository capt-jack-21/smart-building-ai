# Smart Building AI – Project Handover & Development Context

## 1. Project Vision

I am building a Smart Building AI platform using locally hosted open-source LLMs, starting with Qwen.

The long-term objective is to develop a domain-specific Smart Building Foundation Model that understands:

- Project Haystack ontology and semantic tagging.
- Building hierarchies and equipment relationships.
- HVAC systems and building automation.
- BMS integrations, including Niagara.
- IoT devices, LoRaWAN and MQTT.
- Building telemetry and time-series analytics.
- Fault detection, alarm interpretation and troubleshooting.
- CAFM/CMMS integrations and maintenance workflows.
- Building operational intelligence.

The development strategy has two major stages:

**Stage 1: Smart Building AI Platform**

Build an intelligent application around an existing LLM. Give it access to building knowledge, ontology, telemetry and operational APIs through RAG and controlled tool calling.

**Stage 2: Smart Building Foundation Model**

Build domain-specific datasets, evaluate different open-source models, and eventually fine-tune a suitable model using LoRA/QLoRA.

I do NOT want to train an LLM from scratch.

## 2. My Hardware and Development Environment

I have a Windows laptop with:

- OS: Windows
- RAM: 16 GB
- GPU: NVIDIA GeForce RTX 4050 Laptop GPU
- Dedicated VRAM: 6 GB
- NVIDIA Driver: 566.26
- CUDA compatibility reported by NVIDIA-SMI: 12.7

Current local inference environment:

- Ollama installed and working.
- Qwen 3.5 4B installed.
- Model identifier: `qwen3.5:4b`
- Model size: approximately 3.3 GB.
- Local Ollama API: `http://localhost:11434`
- API endpoint tested: `/api/chat`
- Model listing endpoint tested: `/api/tags`

Commands already executed:

```powershell
ollama list
ollama ps
```

Installed model:

```text
NAME          ID              SIZE
qwen3.5:4b    d8b0f5e9760c    3.3 GB
```

The local API successfully returns model responses.

### Hardware performance observed

During inference:

- GPU utilisation: 94%
- GPU memory usage: approximately 4,768 MiB / 6,141 MiB
- GPU temperature: 71°C
- GPU power: approximately 70W
- Model generated approximately 54 tokens/sec in one experiment.

The laptop is sufficient for local development and small-model inference.

Do not recommend expensive GPU purchases at this stage. Use rented GPU infrastructure only when we eventually need fine-tuning.

## 3. My Professional and Technical Background

I have experience as a Senior IoT / Cloud Architect and Platform Architect, including work on a smart building SaaS platform.

My relevant experience includes:

### Smart Building Platform

- Built a smart building data model using Project Haystack concepts.
- Designed a unified entity model for sites, buildings, equipment and points.
- Used PostgreSQL and TimescaleDB.
- Designed multi-tenant architecture.
- Worked on building hierarchies and semantic tagging.

### BMS Integrations

- Niagara BMS integration.
- MQTT alarm ingestion.
- BMS data acquisition and processing.
- Sensor onboarding and telemetry integration.

### IoT Integrations

- LoRaWAN integration with LORIOT as Network Management System.
- Device provisioning.
- Webhook-based status ingestion.
- Device-specific LoRa payload decoding.
- Integration across large building portfolios.

### Data Engineering

- SFTP and API-based ingestion.
- AWS Lambda and ECS.
- S3 raw and processed data layers.
- DynamoDB device mapping.
- TimescaleDB hypertables and performance optimisation.

### Enterprise Integrations

- Built a universal access layer for CAFM/CMMS integrations.
- Worked with Simpro and other maintenance platforms.
- Used Fastify/Node.js and n8n workflows.

Use this background when making architectural recommendations. I prefer practical engineering and production-oriented architecture over generic AI tutorials.

## 4. Work Already Completed

### Experiment 1: Initial Qwen inference

Asked Qwen to explain the relationship between:

- Site
- Building
- HVAC system
- AHU
- Supply air temperature sensor

Qwen returned structured JSON describing a hierarchy and functional relationships.

It demonstrated general smart-building knowledge but incorrectly treated the conceptual hierarchy as a strict Project Haystack hierarchy.

### Experiment 2: Project Haystack entity interpretation

We supplied the following synthetic Haystack-style records:

```json
[
  {
    "id": "site-001",
    "dis": "London Office",
    "site": "m:",
    "geoCity": "London"
  },
  {
    "id": "equip-001",
    "dis": "AHU-01",
    "equip": "m:",
    "ahu": "m:",
    "siteRef": "site-001"
  },
  {
    "id": "point-001",
    "dis": "AHU-01 Supply Air Temperature",
    "point": "m:",
    "temp": "m:",
    "sensor": "m:",
    "air": "m:",
    "unit": "°C",
    "equipRef": "equip-001"
  }
]
```

Qwen correctly identified:

- Site entity.
- AHU equipment entity.
- Temperature measurement point.
- Marker tags such as `site`, `equip`, `ahu`, `point`, `temp`, `sensor` and `air`.
- Equipment reference through `equipRef`.
- Site reference through `siteRef`.

However, it made two important semantic mistakes:

1. It interpreted `equipRef` as a `measures_via` relationship. The reference establishes association with equipment, not necessarily that precise relationship semantics.
2. It interpreted `"sensor": "m:"` as a sensor type. It is only a marker tag.

This demonstrates why we need deterministic ontology validation alongside LLM reasoning.

### Experiment 2 performance

```text
Model: qwen3.5:4b
Prompt Tokens: 291
Generated Tokens: 2664
Generation Speed: 54.07 tokens/sec
Total Duration: 49.72 seconds
```

### Experiment 3: Planned, not yet executed

We prepared a more advanced validation experiment but have not yet received its results.

The test contains:

- A site entity.
- An AHU entity referencing the site.
- A temperature point referencing the AHU.
- A point without an equipment reference.
- A point containing an invalid equipment reference.

The objective is to determine whether Qwen can distinguish:

1. Marker tags.
2. Value tags.
3. Reference tags.
4. Resolved relationships.
5. Missing relationships.
6. Invalid references.

The experiment uses temperature 0 and a maximum output of 1,200 tokens.

Please continue from this point rather than restarting the basic experiments.

## 5. Important Architecture Decisions

We have agreed on the following principles.

### A. Do not depend entirely on the LLM for ontology interpretation

Build a deterministic ontology parser and relationship resolver.

The LLM should be responsible for:

- Natural language understanding.
- Reasoning over structured building context.
- Planning which tools to invoke.
- Explaining findings.
- Generating operational recommendations.

The backend should be responsible for:

- Entity resolution.
- Relationship validation.
- Database queries.
- Tenant isolation.
- Access control.
- Data validation.
- Tool execution.

### B. Separate the knowledge domains

Use:

- Project Haystack as the semantic building ontology.
- PostgreSQL as the application/entity data store.
- TimescaleDB as the operational telemetry store.
- PostgreSQL + pgvector for RAG initially.
- Qwen as the local reasoning model.

### C. Don't train building-specific facts into the LLM

Building configurations and live telemetry change frequently.

Use retrieval and tools for dynamic building data.

Use fine-tuning later for stable domain-specific capabilities such as:

- Haystack semantic interpretation.
- HVAC terminology.
- Alarm classification.
- Equipment troubleshooting patterns.
- Structured output generation.
- Tool-calling behaviour.

## 6. Proposed Smart Building AI Architecture

Initial proposed stack:

| Layer | Technology |
|---|---|
| Frontend | React |
| Backend | Fastify / Node.js |
| Local LLM | Qwen via Ollama |
| Knowledge retrieval | PostgreSQL + pgvector |
| Building ontology | Project Haystack |
| Telemetry | TimescaleDB |
| AI orchestration | Custom tool orchestration initially |
| Deployment | Local development initially |

Conceptual architecture:

```text
Smart Building AI UI
        |
        v
Fastify API / AI Orchestrator
        |
        +------------------+
        |                  |
        v                  v
     Qwen LLM          RAG Engine
        |                  |
        +------------------+
                 |
                 v
       Smart Building Tool Gateway
                 |
       +---------+---------+
       |         |         |
       v         v         v
   Haystack  TimescaleDB  BMS APIs
     API      Telemetry   / Alarms
                 |
                 v
             CAFM/CMMS
```

This is a proposed architecture, not an already implemented system.

## 7. Initial Product Capabilities

Build these in order:

1. Haystack Ontology Intelligence.
2. Building Context Engine.
3. Equipment Intelligence.
4. Telemetry Intelligence.
5. Alarm Intelligence.
6. Maintenance Intelligence.
7. Agentic Building Intelligence.

Example target user interaction:

"Show me all AHUs in Building A, their associated supply air temperature sensors and current readings."

Expected AI behaviour:

1. Understand the question.
2. Resolve Building A.
3. Identify associated AHU entities.
4. Retrieve associated temperature points.
5. Query latest readings from TimescaleDB.
6. Present structured results with entity references and timestamps.
7. Explain missing data or unresolved relationships rather than inventing answers.

## 8. Immediate Next Steps

Please continue with these tasks:

**Task 1 – Complete Experiment 3**

Review the prepared Haystack validation test and help evaluate Qwen's output.

**Task 2 – Build a deterministic Haystack Ontology Intelligence Engine**

Start implementing a small Python or Node.js module that can:

- Parse Haystack records.
- Classify marker, value and reference tags.
- Identify entities.
- Resolve `siteRef` and `equipRef`.
- Detect unresolved references.
- Build equipment-to-point relationships.
- Produce a validated structured representation.

Do not let the LLM invent missing relationships.

**Task 3 – Integrate Qwen**

Connect the ontology engine to Ollama.

Provide the LLM with validated building context and let it answer natural-language questions.

**Task 4 – Build a synthetic smart building**

Start with:

- One site.
- Two buildings.
- Multiple floors.
- Three AHUs.
- Multiple HVAC points.
- Temperature, humidity and energy sensors.
- Sample telemetry.

Use this synthetic environment to test the AI before integrating production data.

**Task 5 – Establish an evaluation framework**

Test:
- Ontology interpretation accuracy.
- Relationship resolution accuracy.
- Invalid reference detection.
- Grounded answer accuracy.
- JSON validity.
- Inference latency.
- Hallucination rate.

## 9. Working Preferences

- I am developing on Windows PowerShell.
- Provide commands that work directly in PowerShell.
- When giving PowerShell API scripts, include `try/catch`, error messages and performance metrics.
- Give complete runnable code rather than fragments where practical.
- Explain architectural decisions, but keep the focus on implementation.
- Avoid unnecessary paid services and expensive infrastructure.
- Build incrementally, testing each module before proceeding.
- Do not assume components have been implemented just because they appear in the proposed architecture.
- Prefer reusable production-quality modules over one-off demonstrations.

## 10. Long-Term Vision

The end goal is not merely a chatbot that knows HVAC terminology.

I want to create a Smart Building AI platform that understands how buildings are structured and operate, can investigate real operational problems, and can interact with different BMS and CAFM systems.

Eventually, I want to develop a domain-specific Smart Building Foundation Model using curated datasets from building ontology, equipment, telemetry, alarms and operational workflows.

Start by continuing from Experiment 3 and then implement the actual Haystack Ontology Intelligence Engine.
