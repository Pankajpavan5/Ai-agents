#!/usr/bin/env bash
# Poll the shared agent branch for a new commit from the peer.
#
# Usage: tools/wait_for_reply.sh [max_seconds] [baseline_sha]
#
# baseline_sha defaults to the current HEAD. Pass it explicitly after you push,
# otherwise the watcher re-reads HEAD only once at startup and will report YOUR
# OWN next push as a peer reply (this actually happened: it flagged bae2245).
set -u
cd /home/user/Ai-agents || exit 1

BRANCH='arena/01a07ba7-ai-agents'
REFSPEC="refs/heads/${BRANCH}:refs/remotes/origin/${BRANCH}"
MAX="${1:-240}"
INTERVAL=10

MINE=$(git rev-parse "${2:-HEAD}")
echo "polling ${BRANCH} — baseline ${MINE:0:7}, max ${MAX}s, every ${INTERVAL}s"

for ((i = 0; i < MAX / INTERVAL; i++)); do
  git fetch origin "$REFSPEC" --force -q 2>/dev/null
  THEIRS=$(git rev-parse "origin/${BRANCH}")
  if [ "$THEIRS" != "$MINE" ]; then
    echo "NEW_REPLY ${THEIRS}"
    git log --oneline "${MINE}..${THEIRS}"
    exit 0
  fi
  sleep "$INTERVAL"
done

echo "NO_REPLY after ${MAX}s (tip still ${MINE:0:7})"
exit 2
