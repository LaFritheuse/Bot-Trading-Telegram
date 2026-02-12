# Workflow Contracts (Multi-Agents)

## Golden rule
The single source of truth is:
1) docs/PROJECT_STATUS.md
2) docs/BUG_LOG.md
3) docs/ARCHITECTURE.md
4) tests/

Agents MUST update docs when they change anything.

## Output formats
### Debugger output (must include)
- Diagnosis (root cause hypothesis)
- Minimal patch plan
- Risk assessment (what could regress)
- Proposed tests

### QA output (must include)
- Tests written
- Commands to run
- Pass/fail summary
- Regression notes

### Release output (must include)
- Version bump suggestion
- CHANGELOG entry
- Artifact list (zip/logs)

