#!/bin/bash
# run_discovery.sh — SOP-01 phase 2: one-command, READ-ONLY discovery of a client's Mac.
# Bundles every audit into ~/client-discovery/<client>-<date>/ and pre-fills the platform register (T-03).
#
#   bash ops/client-discovery/run_discovery.sh <client-slug>
#
# Collects metadata only (names, sizes, dates, versions, account names). Never secret values, never file contents.
# Browser history is reduced to known-platform domains + AI project URLs; full history and search terms are not exported.
# Grant Terminal "Full Disk Access" for the session for complete results; remove it afterwards (T-05).
# macOS bash 3.2 OK.

set -u
CLIENT="${1:?usage: run_discovery.sh <client-slug>}"
HERE="$(cd "$(dirname "$0")" && pwd)"
OPS="$(dirname "$HERE")"
OUTDIR="${OUTDIR:-$HOME/client-discovery/$CLIENT-$(date +%Y%m%d-%H%M%S)}"
mkdir -p "$OUTDIR"
REG="$OUTDIR/T-03-platform-register.csv"
LOG="$OUTDIR/run.log"
n=0
echo "id,layer,platform,account_or_tenant,entity,owner,status,plan_or_sku,monthly_cost,sso,mfa,data_held,sensitivity,evidence,decision,target,wire_in_done,notes" > "$REG"
# ID from the file's line count, so rows added inside piped while-loops (subshells) stay unique
reg() { n=$(wc -l < "$REG" | tr -d ' '); printf 'P-%03d,%s,%s,%s,,,Detected,,,,,,,%s,Decide,,,\n' "$n" "$1" "$2" "$3" "$4" >> "$REG"; }
step() { printf '\n== %s\n' "$*" | tee -a "$LOG"; }

step "1/7 Endpoint (SOP-02 §I)"
EP="$OUTDIR/endpoint.md"
{
  echo "# Endpoint: $(scutil --get ComputerName 2>/dev/null || hostname)"
  echo; echo '```'
  sw_vers 2>/dev/null || uname -a
  echo "FileVault: $(fdesetup status 2>/dev/null || echo unknown)"
  echo "Firewall: $(/usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate 2>/dev/null || echo unknown)"
  echo "Time Machine latest backup: $(tmutil latestbackup 2>/dev/null || echo none/unknown)"
  df -h / /System/Volumes/Data 2>/dev/null
  echo '```'
  echo; echo "## Applications"; echo '```'; ls /Applications "$HOME/Applications" 2>/dev/null | grep -i '\.app$' | sort -u; echo '```'
  echo; echo "## Homebrew"; echo '```'; command -v brew >/dev/null && { brew list --formula -1; echo "-- casks --"; brew list --cask -1; } 2>/dev/null; echo '```'
  echo; echo "## Global npm / pipx / uv tools"; echo '```'
  command -v npm >/dev/null && npm ls -g --depth=0 2>/dev/null
  command -v pipx >/dev/null && pipx list --short 2>/dev/null
  command -v uv >/dev/null && uv tool list 2>/dev/null
  echo '```'
  echo; echo "## Duplicate dev tool installs"; echo '```'
  for t in claude node python3 git gh codex gemini cursor; do c="$(which -a "$t" 2>/dev/null | sort -u | wc -l | tr -d ' ')"; [ "$c" -gt 1 ] && { echo "$t ($c):"; which -a "$t" | sort -u | sed 's/^/  /'; }; done
  echo '```'
  echo; echo "## Login items / LaunchAgents (automations)"; echo '```'
  ls "$HOME/Library/LaunchAgents" /Library/LaunchAgents 2>/dev/null
  osascript -e 'tell application "System Events" to get the name of every login item' 2>/dev/null
  echo '```'
} > "$EP" 2>>"$LOG"
echo "  → $EP"

step "2/7 Accounts and platforms detected (→ T-03)"
# Desktop apps → platforms
for pair in "Claude:L5-ai:Claude" "ChatGPT:L5-ai:ChatGPT" "Perplexity:L5-ai:Perplexity" "Comet:L5-ai:Perplexity Comet" "Grok:L5-ai:Grok" \
            "Cursor:L3-code:Cursor" "Antigravity:L3-code:Google Antigravity" "Windsurf:L3-code:Windsurf" "Visual Studio Code:L3-code:VS Code" \
            "Codex:L3-code:OpenAI Codex" "Devin:L3-code:Devin" "GitHub Desktop:L3-code:GitHub Desktop" \
            "Microsoft Outlook:L2-workspace:Microsoft 365" "Microsoft Teams:L2-workspace:Microsoft 365" "Google Drive:L2-workspace:Google Drive" \
            "OneDrive:L2-workspace:OneDrive" "Dropbox:L2-workspace:Dropbox" "1Password:L0-secrets:1Password" "Okta Verify:L0-identity:Okta" \
            "Notion:L5-saas:Notion" "Slack:L5-saas:Slack" "Linear:L5-saas:Linear" "Obsidian:L5-saas:Obsidian" "Docker:L4-runtime:Docker Desktop"; do
  app="${pair%%:*}"; rest="${pair#*:}"; layer="${rest%%:*}"; plat="${rest#*:}"
  if ls /Applications "$HOME/Applications" 2>/dev/null | grep -qi "^$app.*\.app$"; then reg "$layer" "$plat" "" "app installed: $app"; fi
done
# Cloud sync folders reveal signed-in accounts
for d in "$HOME"/Library/CloudStorage/*; do
  [ -d "$d" ] || continue; b="$(basename "$d")"
  case "$b" in
    GoogleDrive-*) reg L2-workspace "Google Drive" "${b#GoogleDrive-}" "CloudStorage/$b ($(du -sh "$d" 2>/dev/null | cut -f1) local)";;
    OneDrive-*)    reg L2-workspace "OneDrive" "${b#OneDrive-}" "CloudStorage/$b";;
    Dropbox*)      reg L2-workspace "Dropbox" "$b" "CloudStorage/$b";;
    Box-*)         reg L2-workspace "Box" "${b#Box-}" "CloudStorage/$b";;
    *)             reg L2-workspace "$b" "" "CloudStorage/$b";;
  esac
done
[ -d "$HOME/Library/Mobile Documents/com~apple~CloudDocs" ] && reg L2-workspace "iCloud Drive" "$(defaults read MobileMeAccounts Accounts 2>/dev/null | awk -F'"' '/AccountID/{print $2; exit}')" "Mobile Documents/com~apple~CloudDocs"
# Logged-in CLIs → accounts
command -v gh >/dev/null && gh auth status 2>&1 | awk '/Logged in to/ {for(i=1;i<=NF;i++) if($i=="account") print $(i+1)}' | while read -r a; do reg L3-code GitHub "$a" "gh auth status"; done
command -v az >/dev/null && az account show --query user.name -o tsv 2>/dev/null | while read -r a; do reg L0-identity "Microsoft Entra ID / Azure" "$a" "az account show"; done
command -v gcloud >/dev/null && gcloud auth list --format='value(account)' 2>/dev/null | while read -r a; do reg L1-cloud "Google Cloud" "$a" "gcloud auth list"; done
command -v op >/dev/null && op account list --format=json 2>/dev/null | python3 -c 'import json,sys; [print(a.get("url","")+" "+a.get("email","")) for a in json.load(sys.stdin)]' 2>/dev/null | while read -r a; do reg L0-secrets 1Password "$a" "op account list"; done
command -v vercel >/dev/null && vercel whoami 2>/dev/null | tail -1 | while read -r a; do reg L4-runtime Vercel "$a" "vercel whoami"; done
# AI tool config dirs
for pair in ".claude:Claude Code" ".codex:OpenAI Codex CLI" ".cursor:Cursor" ".gemini:Gemini CLI / Antigravity" ".grok:Grok CLI" ".continue:Continue" ".aider.conf.yml:Aider"; do
  p="${pair%%:*}"; [ -e "$HOME/$p" ] && reg L5-ai "${pair#*:}" "" "~/$p present"
done
echo "  → $REG ($(($(wc -l < "$REG") - 1)) rows)"

step "3/7 Browsers (Chrome, Edge, Safari, Brave, Arc, Comet), bookmarks, 1Password titles, Obsidian vaults"
python3 "$HERE/discover_accounts.py" --out "$OUTDIR" 2>>"$LOG" | tee -a "$LOG"
if [ -f "$OUTDIR/platforms-detected.csv" ]; then
  tail -n +2 "$OUTDIR/platforms-detected.csv" | while IFS=, read -r plat layer ev visits last tenants; do
    reg "$layer" "$plat" "$tenants" "$ev ($visits visits, last $last)"
  done
fi

step "4/7 Claude, dev files, AI workspaces, git repos (mac-cleanup audit)"
REPORT="$OUTDIR/mac-audit.md" bash "$OPS/mac-cleanup/audit_claude_files.sh" >>"$LOG" 2>&1 && echo "  → $OUTDIR/mac-audit.md"

step "5/7 Rescue and cleanup previews (dry runs, nothing changes)"
bash "$OPS/mac-cleanup/collect_ai_workspaces.sh" > "$OUTDIR/preview-collect-ai-workspaces.txt" 2>&1
bash "$OPS/mac-cleanup/archive_claude_files.sh" --prune-mcp > "$OUTDIR/preview-archive-claude.txt" 2>&1
echo "  → preview-*.txt"

step "6/7 Cloud stack (uses logged-in CLIs; skips the rest)"
OUT="$OUTDIR/cloud-inventory.md" bash "$OPS/cloud-inventory/inventory_cloud.sh" >>"$LOG" 2>&1 && echo "  → $OUTDIR/cloud-inventory.md"

step "7/7 Storage footprint (SOP-02 §G)"
{
  echo "# Storage footprint"; echo; echo "| Location | Size | Files |"; echo "|---|---|---|"
  for d in "$HOME/Desktop" "$HOME/Documents" "$HOME/Downloads" "$HOME/Code" "$HOME/Library/Mobile Documents/com~apple~CloudDocs" "$HOME"/Library/CloudStorage/*; do
    [ -d "$d" ] || continue
    echo "| \`${d#$HOME/}\` | $(du -sh "$d" 2>/dev/null | cut -f1) | $(find "$d" -type f 2>/dev/null | wc -l | tr -d ' ') |"
  done
  echo; echo "Cross-location duplicate detection: run archive-dedup-playbook inventories (hash-based) against these roots."
} > "$OUTDIR/storage.md" 2>>"$LOG"
echo "  → $OUTDIR/storage.md"

cat > "$OUTDIR/README.md" <<EOF
# Discovery bundle: $CLIENT
Generated $(date) on $(hostname). Read-only; metadata only.

| File | What | SOP-02 sections |
|---|---|---|
| endpoint.md | OS, security, apps, packages, duplicate installs, automations | I, H8 |
| T-03-platform-register.csv | platforms/accounts detected on this Mac (pre-filled; complete with cloud + client input) | A, B, J |
| platforms-detected.csv | platforms seen in browser history/bookmarks, 1Password and Obsidian, with tenant/workspace names | A, B, D, J |
| ai-projects.csv | AI projects, GPTs, Spaces, Gems, notebooks found in browser history | H3 |
| bookmarks.md, 1password-items.csv, obsidian-vaults.md | bookmarks (title + domain), 1Password item titles and domains (no secrets), Obsidian vaults | B, C1, G1 |
| mac-audit.md | Claude/AI tool configs, MCP servers, stray files, git repos, AI workspaces | C3, F3–F4, H4–H6 |
| preview-*.txt | what rescue/cleanup *would* do (dry runs) | F3, H6 |
| cloud-inventory.md | Entra, Azure, GCP, GitHub, Vercel, Cloudflare, 1Password (names only) | B, E, F |
| storage.md | size and file counts per storage location | G1–G2 |
| run.log | errors and skipped steps | |

Next: complete SOP-02, then fill T-04 findings and the T-06 report.
EOF
echo; echo "Discovery bundle: $OUTDIR"
