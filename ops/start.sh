#!/bin/bash
# start.sh — one menu for every consolidation step you run on your Mac. Beginner-friendly.
#
#   cd ~/Code/connectedagents-ai/repo-template && git pull
#   bash ops/start.sh
#
# Every choice is READ-ONLY or a DRY-RUN PREVIEW: nothing is moved, deleted, sent or changed.
# Reports go to ~/ops-reports/<date-time>/ (small text files). Paste them into Claude to decide the next step.
# The real (--apply) runs are never started from here; Claude gives you those one at a time after you approve a plan.
set -u
OPS="$(cd "$(dirname "$0")" && pwd)"
OUT="$HOME/ops-reports/$(date +%Y%m%d-%H%M%S)"
say()  { printf '\n\033[1m%s\033[0m\n' "$*"; }
ok()   { printf '  ✅ %s\n' "$*"; }
warn() { printf '  ⚠️  %s\n' "$*"; }
has()  { command -v "$1" >/dev/null 2>&1; }
report() { mkdir -p "$OUT"; echo "$OUT/$1"; }
# run <report-name> <command...>: show output live and save it
run() { local f; f="$(report "$1")"; shift; "$@" 2>&1 | tee "$f"; ok "Saved: $f"; }

check_setup() {
  say "Checking your tools"
  for t in python3 git gh op dig whois curl; do
    if has "$t"; then ok "$t found"; else warn "$t missing$(case $t in gh) echo ': brew install gh';; op) echo ': brew install 1password-cli';; python3|git) echo ': xcode-select --install';; esac)"; fi
  done
  has gh && { gh auth status >/dev/null 2>&1 && ok "GitHub CLI signed in" || warn "GitHub CLI not signed in: run  gh auth login"; }
  has op && { op whoami >/dev/null 2>&1 && ok "1Password CLI signed in" || warn "1Password CLI not signed in: open 1Password → Settings → Developer → turn on 'Integrate with 1Password CLI'"; }
  if ls "$HOME/Library/Mail" >/dev/null 2>&1; then ok "Terminal has Full Disk Access"; else warn "Terminal lacks Full Disk Access: System Settings → Privacy & Security → Full Disk Access → Terminal, then reopen Terminal"; fi
  ok "Free space on this Mac: $(df -h "$HOME" | awk 'NR==2 {print $4}')"
  n=0; for c in $(which -a claude 2>/dev/null | sort -u); do n=$((n + 1)); done
  [ "$n" -gt 1 ] && warn "You have $n copies of the claude command: $(which -a claude | sort -u | tr '\n' ' ')"
}

menu() {
  cat <<'M'

  What do you want to do?  (everything here is safe: read-only or preview)

   1) Check my setup (tools, sign-ins, disk space)
   2) Find API keys stored in plain text  → the list of keys to ROTATE
   3) Check my domains (DNS, mail, where each one points, expiry)
   4) Audit Claude and other AI-tool files on this Mac
   5) Preview the Claude cleanup (what would be archived)
   6) Preview the duplicate-file cleanup (Mac, cloud folders, iCloud, SSD)
   7) Preview moving GitHub repos into connectedagents-ai
   8) Inventory the cloud stack (Microsoft/Azure, Google Cloud, GitHub, Vercel, Cloudflare, 1Password)
   9) Run 1, 2, 3, 4, 5, 7 and 8 in a row (about 5 minutes), then show where the reports are
   q) Quit
M
  printf '  Type a number and press Return: '
}

do_choice() {
  case "$1" in
    1) run setup.txt check_setup ;;
    2) say "Looking for plain-text API keys (names only, never values)"
       run keys-to-rotate.txt python3 "$OPS/secrets/find_plaintext_keys.py" ;;
    3) say "Checking domains"
       run domains.txt bash "$OPS/domains/check_domains.sh" ;;
    4) say "Auditing Claude and AI-tool files (read-only)"
       REPORT="$(report claude-audit.md)" bash "$OPS/mac-cleanup/audit_claude_files.sh" && ok "Saved: $OUT/claude-audit.md" ;;
    5) say "Previewing the Claude cleanup (dry run: nothing moves)"
       run preview-claude-cleanup.txt bash "$OPS/mac-cleanup/archive_claude_files.sh" --prune-mcp ;;
    6) bash "$OPS/dedup/start_here.sh" ;;
    7) if ! has gh || ! gh auth status >/dev/null 2>&1; then warn "Needs the GitHub CLI signed in (choice 1 shows how)"; return; fi
       say "Previewing the GitHub move (dry run: nothing moves)"
       mkdir -p "$OUT"; (cd "$OUT" && run github-migration-preview.txt bash "$OPS/github-consolidation/migrate_to_connectedagents.sh" Connected-Energy-AI) ;;
    8) say "Inventorying the cloud stack (uses whatever CLIs you're signed in to; skips the rest)"
       f="$(report cloud-inventory.md)"
       OUT="$f" bash "$OPS/cloud-inventory/inventory_cloud.sh" >/dev/null 2>&1 || warn "Some cloud checks failed; see the report"
       ok "Saved: $f" ;;
    9) for c in 1 2 3 4 5 7 8; do do_choice "$c"; done
       say "All done. Reports are in: $OUT"
       open "$OUT" 2>/dev/null || true
       echo "  Next: open keys-to-rotate.txt first and rotate those keys. Then paste the other reports into Claude." ;;
    q|Q) exit 0 ;;
    *) warn "Please type one of the numbers shown." ;;
  esac
}

say "Consolidation menu: nothing here changes your Mac, accounts or files."
if [ $# -ge 1 ]; then do_choice "$1"; exit 0; fi
while true; do
  menu; read -r choice || exit 0
  do_choice "$choice"
done
