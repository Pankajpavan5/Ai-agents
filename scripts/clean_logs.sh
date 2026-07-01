#!/usr/bin/env bash
# clean_logs.sh — Truncates session_logs.md and episodic.md files back to their
# header template, for starting a fresh test run. Long-term/semantic memory is untouched.
# Usage: ./scripts/clean_logs.sh [--yes]
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ "${1:-}" != "--yes" ]]; then
  echo "This will clear all agents' session_logs.md and episodic.md content."
  echo "Re-run with --yes to confirm."
  exit 1
fi

for agent_dir in agents/*/; do
  : > "${agent_dir}storage/session_logs.md"
  : > "${agent_dir}memory/episodic.md"
  echo "Cleared logs for $(basename "$agent_dir")"
done

echo "Done."
