# System Architecture

> Overview of how the AI Arena multi-agent repo is structured and how information flows through it.

## Agents
Three specialized agents collaborate on every task:
- **Analyst** — understands and scopes the task.
- **Optimizer** — refines the approach/solution.
- **Debugger** — validates and finalizes.

Each agent has an identical internal structure:
```
agents/<agent_name>/
├── agent_info.md      # Role definition, responsibilities
├── memory/
│   ├── episodic.md    # Recent task history
│   ├── semantic.md    # Learned patterns
│   └── long_term.md   # Core knowledge
└── storage/
    └── session_logs.md # Execution traces
```

## Shared Knowledge Layer
`ai_brain/` sits above all agents and holds knowledge that has been generalized beyond a single agent's context — problem/solution pairs and system-wide insights.

## Task Lifecycle
```
tasks/pending/  --Analyst picks up-->  tasks/assigned/
                                             |
                                    Analyst -> Optimizer -> Debugger
                                             |
                              tasks/complete/  +  tasks/reports/
```

## Communication
Agents don't call each other directly — they communicate through files in `message_system/`:
- Point-to-point handoffs: `agent_messages/<from>_to_<to>.md`
- System-wide announcements: `agent_messages/broadcast.md`
- Full audit trail: `system_log.md`

## Automation
`scripts/` contains helper scripts to bootstrap agent folders, run an agent loop, and clean up stale task/log files.
