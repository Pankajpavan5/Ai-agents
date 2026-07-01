# Operational Rules

> Rules that all agents in the AI Arena system must follow.

1. **No task skips validation.** Every task must pass through the Debugger before being marked complete.
2. **Memory hygiene.** Agents write raw traces to `storage/session_logs.md`, summarize into `memory/episodic.md`, distill recurring patterns into `memory/semantic.md`, and only promote durable, high-confidence knowledge to `memory/long_term.md`.
3. **Shared knowledge first.** Before starting a task, check `ai_brain/` for relevant prior solutions or insights.
4. **Communicate via the message system.** Agent-to-agent handoffs must be logged in `message_system/agent_messages/` and reflected in `message_system/system_log.md`.
5. **No secrets in the repo.** Credentials, tokens, and API keys must never be committed. Use `.gitignore` and environment variables.
6. **One task, one file.** Each task lives in exactly one file at a time, moved between `tasks/pending/`, `tasks/assigned/`, and `tasks/complete/` as its state changes — never duplicated.
7. **Escalate ambiguity.** If a task is unclear or under-specified, the Analyst must flag it rather than guess.
8. **Document trade-offs.** Any optimization or fix that trades one quality for another (speed vs. readability, cost vs. accuracy) must be documented at the point of change.
