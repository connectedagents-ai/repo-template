#!/bin/bash
# collect_ai_workspaces.sh — rescue code that AI tools left in their own scratch folders
# (Antigravity, Codex, Cursor, Grok, Devin, Copilot) into ONE inbox repo instead of N new repos.
#
#   bash collect_ai_workspaces.sh           # DRY RUN: shows what would be copied
#   bash collect_ai_workspaces.sh --apply   # copy into ~/Code/connectedagents-ai/ai-workspace-inbox/<tool>/<folder>
#
# Copies (never moves) and skips dependencies, build output and secrets. Folders that are already git
# repos with a remote are NOT copied — they are listed so you push or migrate them instead.
# After --apply: review, run `git status`, commit, and push the inbox repo. Then triage each folder:
# promote to its product repo, or leave it archived in the inbox.

set -u
APPLY=0; [ "${1:-}" = "--apply" ] && APPLY=1
command -v rsync >/dev/null || { echo "rsync is required (ships with macOS)" >&2; exit 1; }
INBOX="${INBOX:-$HOME/Code/connectedagents-ai/ai-workspace-inbox}"

EXCLUDES="--exclude=node_modules --exclude=.venv --exclude=venv --exclude=__pycache__ --exclude=.next --exclude=dist --exclude=build --exclude=.turbo --exclude=.DS_Store --exclude=.env --exclude=.env.* --exclude=*.pem --exclude=*.key --exclude=*.p12 --exclude=id_rsa* --exclude=id_ed25519* --exclude=*.sqlite --exclude=*.log"

MIN_FREE_GB="${MIN_FREE_GB:-15}"
# size (KB) of what rsync will actually copy: same excluded dirs/files as EXCLUDES below
copy_size_kb() {
  python3 - "$1" <<'PYSZ'
import fnmatch, os, sys
dirs = {"node_modules", ".venv", "venv", "__pycache__", ".next", "dist", "build", ".turbo", ".git"}
files = [".DS_Store", ".env", ".env.*", "*.pem", "*.key", "*.p12", "id_rsa*", "id_ed25519*", "*.sqlite", "*.log"]
total = 0
for dp, dn, fn in os.walk(sys.argv[1]):
    dn[:] = [d for d in dn if d not in dirs]
    for f in fn:
        if not any(fnmatch.fnmatch(f, p) for p in files):
            try:
                total += os.lstat(os.path.join(dp, f)).st_size
            except OSError:
                pass
print(total // 1024)
PYSZ
}   # never let a copy leave the destination disk with less than this free
PLANNED=""

[ "$APPLY" = 1 ] && mkdir -p "$INBOX" && [ ! -d "$INBOX/.git" ] && git -C "$INBOX" init -q -b main && \
  printf '# AI workspace inbox\n\nCode rescued from AI tool scratch folders. Triage: promote to a product repo or leave archived here.\n' > "$INBOX/README.md"

for spec in \
  "antigravity|$HOME/.gemini/antigravity/scratch" \
  "antigravity|$HOME/.gemini/antigravity/playground" \
  "antigravity|$HOME/.antigravity/projects" \
  "codex|$HOME/.codex/worktrees" \
  "codex|$HOME/Documents/Codex" \
  "cursor|$HOME/.cursor/worktrees" \
  "cursor|$HOME/Documents/Cursor" \
  "grok|$HOME/.grok/workspaces" \
  "grok|$HOME/.grok/projects" \
  "devin|$HOME/Devin" \
  "copilot|$HOME/Documents/Copilot"; do
  tool="${spec%%|*}"; parent="${spec#*|}"
  [ -d "$parent" ] || continue
  for d in "$parent"/*/; do
    [ -d "$d" ] || continue; d="${d%/}"; name="$(basename "$d")"
    if [ -e "$d/.git" ] && [ -n "$(git -C "$d" remote 2>/dev/null | head -1)" ]; then   # repo or worktree with any remote
      printf 'push-it   %-12s %s  (git repo with remote: commit + push there, then migrate)\n' "$tool" "${d#$HOME/}"
      continue
    fi
    printf 'collect   %-12s %s → %s  (%s MB to copy)\n' "$tool" "${d#$HOME/}" "${INBOX#$HOME/}/$tool/$name" "$(( $(copy_size_kb "$d") / 1024 ))"
    PLANNED="$PLANNED
$d"
    if [ "$APPLY" = 1 ]; then
      need_kb=$(copy_size_kb "$d")
      free_kb=$(df -k "$(dirname "$INBOX")" | awk 'NR==2 {print $4}')
      if [ $((free_kb - need_kb)) -lt $((MIN_FREE_GB * 1024 * 1024)) ]; then
        echo "  ✋ STOP: copying ${d#$HOME/} ($((need_kb / 1024)) MB) would leave less than ${MIN_FREE_GB} GB free. Nothing more will be copied." >&2
        echo "     Set INBOX=/Volumes/<SSD>/ai-workspace-inbox to collect onto an external drive instead." >&2
        exit 1
      fi
      mkdir -p "$INBOX/$tool/$name"
      # shellcheck disable=SC2086
      rsync -a $EXCLUDES --exclude=.git "$d/" "$INBOX/$tool/$name/"
    fi
  done
done

if [ "$APPLY" = 1 ]; then
  echo
  echo "Copied into $INBOX. Before committing, scan for secrets:"
  echo "  grep -rEn '(sk-[A-Za-z0-9]{20,}|xai-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{30,}|AKIA[0-9A-Z]{16}|-----BEGIN .*PRIVATE KEY)' \"$INBOX\" | cut -c1-120"
  echo "Then: gh repo create connectedagents-ai/ai-workspace-inbox --private --source \"$INBOX\" --push"
else
  echo; echo "Dry run. Re-run with --apply to copy."
fi
