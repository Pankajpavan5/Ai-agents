#!/usr/bin/env bash
# new_task.sh — Creates a new task file from the template in tasks/pending/.
# Usage: ./scripts/new_task.sh "Short task title"
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ $# -lt 1 ]; then
  echo "Usage: $0 \"Task title\""
  exit 1
fi

TITLE="$1"
SLUG=$(echo "$TITLE" | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9' '-' | sed 's/-\+/-/g; s/^-//; s/-$//')
DATE=$(date +%Y-%m-%d)
COUNT=$(find tasks/pending tasks/assigned tasks/complete -name "TASK-*.md" 2>/dev/null | wc -l | tr -d ' ')
ID=$(printf "TASK-%03d" $((COUNT + 1)))
FILE="tasks/pending/${ID}-${SLUG}.md"

sed -e "s/<Title>/$TITLE/" \
    -e "s/TASK-XXX/$ID/" \
    -e "s/<YYYY-MM-DD>/$DATE/" \
    "system/templates/task_template.md" > "$FILE"

echo "Created $FILE"
