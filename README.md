# AI Arena Repo

A multi-agent system scaffold where specialized agents (Analyst, Optimizer, Debugger) collaborate on tasks using a shared knowledge base, structured memory, and a file-based message system.

## Structure

```
ai-arena-repo/
├── agents/                 # Per-agent role, memory, and storage
│   ├── analyst/
│   ├── optimizer/
│   └── debugger/
├── ai_brain/                # Shared knowledge base across all agents
├── tasks/                   # Task lifecycle: pending -> assigned -> complete -> reports
├── message_system/          # Inter-agent communication logs
├── system/                  # Config, rules, architecture docs, templates
├── scripts/                 # Setup and automation scripts
├── README.md
└── .gitignore
```

## Agents

| Agent | Role |
|---|---|
| **Analyst** | Breaks down and scopes incoming tasks, gathers context |
| **Optimizer** | Refines and improves solutions for performance/efficiency |
| **Debugger** | Validates, tests, and signs off on completed work |

Each agent maintains its own memory hierarchy:
- `memory/episodic.md` — recent task history
- `memory/semantic.md` — learned patterns
- `memory/long_term.md` — durable core knowledge
- `storage/session_logs.md` — raw execution traces

## Shared Knowledge (`ai_brain/`)
- `ai_brain.md` — combined knowledge base / index
- `problem_solutions.md` — catalog of issues and fixes
- `system_insights.md` — collective, system-wide learnings

## Task Flow
```
tasks/pending -> tasks/assigned -> (Analyst -> Optimizer -> Debugger) -> tasks/complete -> tasks/reports
```

## Communication
Agents communicate via files under `message_system/`:
- `agent_messages/analyst_to_optimizer.md`
- `agent_messages/optimizer_to_debugger.md`
- `agent_messages/broadcast.md`
- `system_log.md` — full audit trail

## Getting Started
```bash
./scripts/setup.sh              # verify/create the full folder structure
./scripts/new_task.sh "Title"   # create a new task in tasks/pending/
```

## Rules & Architecture
See [`system/rules.md`](system/rules.md) and [`system/architecture.md`](system/architecture.md) for the full operating model.
