# Smart Building AI — Project Context

## Project Vision
Build a domain-specific Smart Building AI platform, with the long-term objective of developing a Smart Building Foundation Model.

## Development Environment
- IDE: Visual Studio Code
- AI development assistant: ChatGPT
- Local LLM: Qwen 3.5 4B
- Model runtime: Ollama
- OS: Windows
- Hardware: 16 GB RAM, NVIDIA RTX 4050 (6 GB VRAM)

## Technology Stack
- Backend: Python initially, Fastify/Node.js for application APIs
- Frontend: React
- Ontology: Project Haystack
- Database: PostgreSQL
- Time-series: TimescaleDB
- Vector search: pgvector
- Local inference: Qwen through Ollama

## Engineering Principles
1. Use deterministic ontology parsing and validation.
2. Never allow LLMs to invent entity relationships.
3. Building data remains the source of truth.
4. Use RAG for domain knowledge.
5. Use controlled tools for live telemetry and integrations.
6. Enforce tenant isolation in the backend.
7. Build modular, testable, production-quality components.
8. Evaluate model outputs against ground truth.

## Initial Priority
Build the deterministic Haystack Ontology Intelligence Engine before developing the complete AI application.

## Development Workflow
- Use ChatGPT for architecture, code generation, debugging and reviews.
- Use VS Code as the primary development environment.
- Use Qwen locally for model experimentation and evaluation.
- Test each module before moving to the next.
- Document important architectural decisions.
- Never commit secrets, credentials or model weights.
