#!/bin/bash
# refresh.sh — keep the agent home current: merge memory, regenerate every README/memory/tools file, install into each tool.
#
#   bash ops/agents/refresh.sh --root ~/Code/connectedagents-ai/<private-repo>            # DRY RUN
#   bash ops/agents/refresh.sh --root ~/Code/connectedagents-ai/<private-repo> --apply    # nightly job / hook / by hand
#   bash ops/agents/refresh.sh --root <repo> --apply --no-sync                            # CI: regenerate files only
#
# Triggers (docs/AGENT-FILESYSTEM.md): Claude Code SessionEnd hook, nightly launchd job, CI on push to the private repo.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="" APPLY="" SYNC=1
while [ $# -gt 0 ]; do
  case "$1" in
    --root) ROOT="$2"; shift 2 ;;
    --apply) APPLY="--apply"; shift ;;
    --no-sync) SYNC=0; shift ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done
[ -n "$ROOT" ] || { echo "usage: refresh.sh --root <agent home> [--apply] [--no-sync]" >&2; exit 2; }
python3 "$HERE/agent_fs.py" memory merge --root "$ROOT" $APPLY
python3 "$HERE/agent_fs.py" render --root "$ROOT" $APPLY
if [ "$SYNC" = 1 ]; then python3 "$HERE/agent_fs.py" sync --root "$ROOT" $APPLY; fi
