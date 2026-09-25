#!/bin/bash
# run_dedup.sh — DRY-RUN dedup across every surface on this Mac, one parallel scanner per surface, then one merge.
#
#   bash ops/dedup/run_dedup.sh                      # all surfaces → ~/dedup-runs/<stamp>/ (report only)
#   OUT=/Volumes/ExtremeSSD/dedup-runs bash ops/dedup/run_dedup.sh   # keep reports off the internal disk
#   SSD_ROOT="/Volumes/Extreme SSD" OUT=... bash ops/dedup/run_dedup.sh   # also scan the SSD itself (read-only);
#     SSD copies are preferred as keepers, so Mac copies of SSD files show up as the ones to archive
#   CLOUD_REMOTES="gdrive-powerconnection: pcloud:" OUT=... bash ops/dedup/run_dedup.sh   # also list cloud accounts
#     through their APIs (rclone; set up with connect_cloud.sh). Uses the provider's stored checksums: nothing downloads.
#   SKIP_CLOUDSTORAGE="GoogleDrive-me@x.com OneDrive-OneWishLabs" ...   # local sync folders whose account is already in
#     CLOUD_REMOTES, so the same files aren't listed twice (start_here.sh asks). Only the named folders are skipped.
#     pCloud Drive mounts are never walked.
#   SKIP_ICLOUD=1 ...   # leave iCloud Drive out (e.g. when macOS's iCloud sync is slow and the scan stalls there)
#
# Surfaces: mac-local (Desktop, Documents, Downloads, ~/Code), each ~/Library/CloudStorage/* folder (Google Drive,
# OneDrive, Dropbox, Box), and iCloud Drive (metadata only: cloud-only files are never downloaded or hashed).
# Nothing moves. Review PLAN.md, then apply with dedup_apply.py (archive target must be an external volume).
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
RUN="${OUT:-$HOME/dedup-runs}/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$RUN"
echo "Dedup run (dry run) → $RUN"
echo "Free space on internal disk: $(df -h "$HOME" | awk 'NR==2 {print $4}')"

pids=""
label() { basename "$1" | tr 'A-Z' 'a-z' | sed 's/[^a-z0-9._-]/-/g'; }
scan() { python3 "$HERE/dedup_scan.py" --out "$RUN" "$@" >>"$RUN/scan.log" 2>&1 & pids="$pids $!"; }

scan --surface mac-local --root "$HOME/Desktop" --root "$HOME/Documents" --root "$HOME/Downloads" --root "$HOME/Code"
for r in ${CLOUD_REMOTES:-}; do
  python3 "$HERE/cloud_inventory.py" --remote "$r" --out "$RUN" >>"$RUN/scan.log" 2>&1 & pids="$pids $!"
done
cloud_folder_skipped() {
  local b; b="$(basename "$1")"
  case "$b" in *[Pp][Cc]loud*) return 0;; esac  # pCloud Drive is a virtual drive: reading files would download them
  case " ${SKIP_CLOUDSTORAGE:-} " in *" $b "*) return 0;; esac
  return 1
}
for d in "$HOME"/Library/CloudStorage/*; do
  [ -d "$d" ] || continue
  cloud_folder_skipped "$d" && { echo "  skip $d (listed through its API instead)" >> "$RUN/scan.log"; continue; }
  scan --surface "$(label "$d")" --root "$d"
done
[ -n "${SSD_ROOT:-}" ] && [ -d "$SSD_ROOT" ] && scan --surface ssd --root "$SSD_ROOT"
ICLOUD="$HOME/Library/Mobile Documents/com~apple~CloudDocs"
if [ "${SKIP_ICLOUD:-0}" = 1 ]; then echo "  skip iCloud Drive (SKIP_ICLOUD=1)" >> "$RUN/scan.log"
elif [ -d "$ICLOUD" ]; then scan --surface icloud-drive --root "$ICLOUD"; fi

fail=0
for p in $pids; do wait "$p" || fail=1; done
cat "$RUN/scan.log"
[ "$fail" = 0 ] || echo "⚠ one or more scanners failed; see $RUN/scan.log"

PREFER="$( [ -n "${SSD_ROOT:-}" ] && echo "--prefer ssd") --prefer mac-local"
for d in "$HOME"/Library/CloudStorage/*; do [ -d "$d" ] && ! cloud_folder_skipped "$d" && PREFER="$PREFER --prefer $(label "$d")"; done
# shellcheck disable=SC2086
python3 "$HERE/dedup_merge.py" --in "$RUN" $PREFER --prefer icloud-drive
echo
echo "Photos: the Photos library is not scanned (use Photos → Utilities → Duplicates, built into macOS)."
echo "Next: review $RUN/PLAN.md, then dry-run: python3 $HERE/dedup_apply.py --plan $RUN/duplicates.csv --archive-root /Volumes/<SSD>/Dedup-Archive"
