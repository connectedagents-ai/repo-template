#!/bin/bash
# start_here.sh — beginner-friendly, guided DRY RUN of the dedup. Nothing is moved or deleted.
#
#   cd ~/Code/connectedagents-ai/repo-template && git pull
#   bash ops/dedup/start_here.sh
#
# It checks your setup, asks which external drive to use, runs the scan, opens the report and shows a preview.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
VOLUMES="${VOLUMES_DIR:-/Volumes}"
say()  { printf '\n\033[1m%s\033[0m\n' "$*"; }
ok()   { printf '  ✅ %s\n' "$*"; }
warn() { printf '  ⚠️  %s\n' "$*"; }
stop() { printf '\n  ❌ %s\n\n' "$*"; exit 1; }

say "Dedup preview — nothing will be moved or deleted."

say "1/5 Checking your setup"
command -v python3 >/dev/null 2>&1 && ok "python3 found" || stop "python3 is missing. Run:  xcode-select --install   then run this script again."
if ls "$HOME/Library/Mail" >/dev/null 2>&1 || ls "$HOME/Library/Safari" >/dev/null 2>&1; then
  ok "Terminal has Full Disk Access"
else
  warn "Terminal may not have Full Disk Access (some folders will be skipped)."
  warn "Fix: System Settings → Privacy & Security → Full Disk Access → turn on Terminal, then quit and reopen Terminal."
fi
ok "Free space on this Mac: $(df -h "$HOME" | awk 'NR==2 {print $4}')"

say "2/5 Choose your external drive (the report is saved there, not on your Mac)"
drives=()
for v in "$VOLUMES"/*; do
  [ -d "$v" ] || continue
  case "$(basename "$v")" in "Macintosh HD"|"Macintosh HD - Data"|Recovery|Preboot|VM|com.apple.*) continue;; esac
  drives+=("$v")
done
[ ${#drives[@]} -gt 0 ] || stop "No external drive found. Plug in your SSD, wait a few seconds, and run this script again."
i=1
for d in "${drives[@]}"; do printf '   %d) %s  (%s free)\n' "$i" "$(basename "$d")" "$(df -h "$d" | awk 'NR==2 {print $4}')"; i=$((i + 1)); done
if [ ${#drives[@]} -eq 1 ]; then
  choice=1; ok "Using the only drive found: $(basename "${drives[0]}")"
else
  printf '  Type the number of your SSD and press Return: '; read -r choice
fi
case "$choice" in ''|*[!0-9]*) stop "Please type just a number, like 1.";; esac
[ "$choice" -ge 1 ] && [ "$choice" -le ${#drives[@]} ] || stop "That number isn't in the list."
SSD="${drives[$((choice - 1))]}"
[ -w "$SSD" ] || stop "Can't write to $(basename "$SSD"). Check the drive isn't read-only (Finder → Get Info)."
ok "Report will be saved on: $(basename "$SSD")"

printf '\n  Also scan the SSD itself, to find Mac files that are copies of SSD files? (y/n): '; read -r inc
case "$inc" in y|Y|yes|YES) SSD_ROOT="$SSD"; ok "The SSD will be scanned too (read-only). SSD copies are kept; Mac copies are the ones proposed for archive.";;
  *) SSD_ROOT=""; ok "Scanning the Mac, cloud folders and iCloud only.";; esac

CLOUD_REMOTES=""
if command -v rclone >/dev/null 2>&1 && [ -n "$(rclone listremotes 2>/dev/null)" ]; then
  printf '\n  Also check these connected cloud accounts (Google Drive / pCloud)? Nothing is downloaded.\n'
  rclone listremotes | sed 's/^/     /'
  printf '  Include them? (y/n): '; read -r inc_cloud
  case "$inc_cloud" in y|Y|yes|YES) CLOUD_REMOTES="$(rclone listremotes | tr '\n' ' ')"; ok "Cloud accounts included (listed through their APIs).";; esac
else
  ok "No Google Drive / pCloud accounts connected (optional: bash ops/dedup/connect_cloud.sh, then run this again)."
fi

say "3/5 Scanning (this can take a while — leave this window open)"
CLOUD_REMOTES="$CLOUD_REMOTES" SSD_ROOT="$SSD_ROOT" OUT="$SSD/dedup-runs" bash "$HERE/run_dedup.sh" || stop "The scan stopped with an error. Copy everything above and paste it into Claude."
RUN="$(ls -td "$SSD"/dedup-runs/*/ 2>/dev/null | head -1)"; RUN="${RUN%/}"
[ -f "$RUN/PLAN.md" ] || stop "No report was produced. Copy everything above and paste it into Claude."

say "4/5 Your report"
cat "$RUN/PLAN.md"
open "$RUN" 2>/dev/null || true
ok "Opened the report folder in Finder: $RUN"

say "5/5 Preview of what WOULD be archived (still nothing moves)"
python3 "$HERE/dedup_apply.py" --plan "$RUN/duplicates.csv" --archive-root "$SSD/Dedup-Archive" | tail -15
[ -n "$CLOUD_REMOTES" ] && { echo; echo "  Inside your cloud accounts:"; python3 "$HERE/cloud_apply.py" --plan "$RUN/duplicates.csv" | tail -8; }

say "Done. Nothing was moved."
echo "  Next: paste the PLAN.md summary above into Claude and decide together."
echo "  Only when you approve, the real run is:"
echo "    python3 \"$HERE/dedup_apply.py\" --plan \"$RUN/duplicates.csv\" --archive-root \"$SSD/Dedup-Archive\" --apply"
echo "  (it keeps an undo script; legal-flagged and iCloud files are never moved automatically)"
