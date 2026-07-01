# System Configuration

> High-level configuration reference for the AI Arena multi-agent system. (Non-secret settings only — never store API keys/tokens here.)

## Agents
| Agent | Role | Status |
|---|---|---|
| Analyst | Research & task breakdown | Active |
| Optimizer | Refinement & performance | Active |
| Debugger | Validation & QA | Active |

## Task Flow
```
pending -> assigned -> (analyst -> optimizer -> debugger) -> complete -> reports
```

## Directories
- `agents/` — per-agent role definitions, memory, and logs.
- `ai_brain/` — shared knowledge base across all agents.
- `tasks/` — task lifecycle (pending, assigned, complete, reports).
- `message_system/` — inter-agent communication.
- `system/` — rules, architecture docs, and templates.
- `scripts/` — automation/setup scripts.

## Environment / Secrets
Do not commit tokens, API keys, or credentials to this repo. Use environment variables or a secrets manager instead.
