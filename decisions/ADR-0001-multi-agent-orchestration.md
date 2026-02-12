# ADR-0001 — Multi-agent orchestration using n8n + GitHub

## Context
We need persistent project memory, reproducibility, and non-regression.

## Decision
Use n8n to orchestrate specialized LLM agents. Persist state in GitHub docs and artifacts.

## Consequences
- Works even if n8n is replaced later (GitHub remains).
- Requires discipline: docs + tests are mandatory.

