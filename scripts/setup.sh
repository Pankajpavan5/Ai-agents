#!/usr/bin/env bash
# setup.sh — Bootstraps the AI Arena repo structure.
# Safe to re-run: only creates missing directories/files, never overwrites existing ones.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

AGENTS=("analyst" "optimizer" "debugger")

echo "Setting up AI Arena repo structure at: $ROOT_DIR"

for agent in "${AGENTS[@]}"; do
  mkdir -p "agents/$agent/memory" "agents/$agent/storage"
  [ -f "agents/$agent/agent_info.md" ] || cp "system/templates/agent_template.md" "agents/$agent/agent_info.md"
  for f in episodic semantic long_term; do
    touch "agents/$agent/memory/$f.md"
  done
  touch "agents/$agent/storage/session_logs.md"
done

mkdir -p ai_brain tasks/pending tasks/assigned tasks/complete tasks/reports
mkdir -p message_system/agent_messages
mkdir -p system/templates scripts

echo "Done. Directory structure verified/created."
