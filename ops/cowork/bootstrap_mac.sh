#!/bin/bash
# bootstrap_mac.sh — get this Mac ready for Claude Code / Cowork to work on the owner's behalf.
#
#   bash ops/cowork/bootstrap_mac.sh           # PREVIEW (default): checks every tool, changes nothing
#   bash ops/cowork/bootstrap_mac.sh --apply   # install missing tools with Homebrew + install the global agent rules
#
# The preview is the pre-job checklist: READY / MISSING / NEEDS YOU for each tool, with the fix. --apply only installs
# Homebrew packages and copies rule files (any existing file is kept as <name>.bak-<stamp>). Logins stay with the owner.
# Log: ~/ops-reports/bootstrap-<stamp>.log. macOS bash 3.2 OK.
set -u
APPLY=0; [ "${1:-}" = "--apply" ] && APPLY=1
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
SSD="${SSD:-/Volumes/Extreme SSD}"
STAMP="$(date +%Y%m%d-%H%M%S)"
mkdir -p "$HOME/ops-reports"
LOG="$HOME/ops-reports/bootstrap-$STAMP.log"
missing="" needs_you=0

say() { echo "$*" | tee -a "$LOG"; }
have() { command -v "$1" >/dev/null 2>&1; }

check_tool() {  # command, brew package
  if have "$1"; then say "READY     $1"; else say "MISSING   $1  (fix: brew install $2)"; missing="$missing $2"; fi
}

say "Pre-job checklist for $(hostname) — $(date)"
say "Repo: $REPO"
if have brew; then say "READY     brew"; else
  say "NEEDS YOU brew  (paste: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\")"
  needs_you=1
fi
check_tool git git
check_tool gh gh
check_tool node node
check_tool pnpm pnpm
check_tool python3 python
check_tool uv uv
check_tool jq jq
check_tool rclone rclone
check_tool op 1password-cli
if have claude; then say "READY     claude"; else
  say "NEEDS YOU claude  (paste: curl -fsSL https://claude.ai/install.sh | bash)"; needs_you=1
fi
if have gh && ! gh auth status >/dev/null 2>&1; then
  say "NEEDS YOU gh login  (paste: gh auth login --hostname github.com --git-protocol ssh --web)"; needs_you=1
fi
if have op && ! op whoami >/dev/null 2>&1; then
  say "NEEDS YOU 1Password CLI  (1Password app → Settings → Developer → Integrate with 1Password CLI)"; needs_you=1
fi
if [ -d "$SSD" ]; then say "READY     SSD at $SSD"; else say "NEEDS YOU plug in the SSD ($SSD)"; needs_you=1; fi

install_rules() {  # source file, destination
  mkdir -p "$(dirname "$2")"
  if [ -f "$2" ] && cmp -s "$1" "$2"; then say "SAME      $2"; return; fi
  [ -f "$2" ] && cp -p "$2" "$2.bak-$STAMP" && say "BACKUP    $2.bak-$STAMP"
  cp "$1" "$2" && say "INSTALLED $2"
}

RULES="$(mktemp)"; trap 'rm -f "$RULES"' EXIT
{ echo "# Owner rules for every agent on this Mac (from $REPO/AGENTS.md; re-run bootstrap_mac.sh --apply to refresh)"
  echo; sed -n '/^## 5\. /,$p' "$REPO/AGENTS.md"; } > "$RULES"

if [ "$APPLY" = 1 ]; then
  say ""; say "Applying…"
  if [ -n "$missing" ] && have brew; then
    for p in $missing; do
      if [ "$p" = 1password-cli ]; then brew install --cask 1password-cli >>"$LOG" 2>&1; else brew install "$p" >>"$LOG" 2>&1; fi \
        && say "INSTALLED $p" || say "FAILED    $p (see $LOG)"
    done
  fi
  install_rules "$REPO/ops/mac-cleanup/templates/CLAUDE.md" "$HOME/.claude/CLAUDE.md"
  install_rules "$REPO/ops/mac-cleanup/templates/settings.json" "$HOME/.claude/settings.json"
  install_rules "$RULES" "$HOME/.codex/AGENTS.md"
  install_rules "$RULES" "$HOME/.gemini/GEMINI.md"
  say ""; say "Done. Undo any rule file by copying its .bak-$STAMP back. Log: $LOG"
else
  say ""
  say "Preview only: nothing changed. Next: bash ops/cowork/bootstrap_mac.sh --apply"
  say "It would install:${missing:- nothing} · and the agent rules into ~/.claude, ~/.codex, ~/.gemini"
fi
[ "$needs_you" = 1 ] && say "Some lines say NEEDS YOU: do those yourself (paste the command shown), then re-run."
exit 0
