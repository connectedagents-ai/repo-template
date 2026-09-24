#!/bin/bash
# run_dedup.sh — DRY-RUN dedup across every surface on this Mac, one parallel scanner per surface, then one merge.
#
#   bash ops/dedup/run_dedup.sh                      # all surfaces → ~/dedup-runs/<stamp>/ (report only)
#   OUT=/Volumes/ExtremeSSD/dedup-runs bash ops/dedup/run_dedup.sh   # keep reports off the internal disk
#   SSD_ROOT="/Volumes/Extreme SSD" OUT=... bash ops/dedup/run_dedup.sh   # also scan the SSD itself (read-only);
#     SSD copies are preferred as keepers, so Mac copies of SSD files show up as the ones to archive
#   CLOUD_REMOTES="gdrive-powerconnection: pcloud:" OUT=... bash ops/dedup/run_dedup.sh   # also list cloud accounts
#     through their APIs (rclone; set up with connect_cloud.sh). Uses the provider's stored checksums: nothing downloads.
#     When a Google Drive remote is listed, the ~/Library/CloudStorage/GoogleDrive-* folders are not scanned too
#     (the same files would otherwise look like duplicates of themselves). pCloud Drive mounts are never walked.
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
DRIVE_VIA_API=0
for r in ${CLOUD_REMOTES:-}; do
  case "$(rclone listremotes --long 2>/dev/null | awk -v n="$r" '$1 == n {print $2}')" in drive) DRIVE_VIA_API=1;; esac
  python3 "$HERE/cloud_inventory.py" --remote "$r" --out "$RUN" >>"$RUN/scan.log" 2>&1 & pids="$pids $!"
done
cloud_folder_skipped() {
  case "$(basename "$1")" in
    GoogleDrive-*) [ "$DRIVE_VIA_API" = 1 ];;
    *[Pp][Cc]loud*) true;;  # pCloud Drive is a virtual drive: reading files would download them. Use its API instead
    *) false;;
  esac
}
for d in "$HOME"/Library/CloudStorage/*; do
  [ -d "$d" ] || continue
  cloud_folder_skipped "$d" && { echo "  skip $d (listed through its API instead)" >> "$RUN/scan.log"; continue; }
  scan --surface "$(label "$d")" --root "$d"
done
[ -n "${SSD_ROOT:-}" ] && [ -d "$SSD_ROOT" ] && scan --surface ssd --root "$SSD_ROOT"
ICLOUD="$HOME/Library/Mobile Documents/com~apple~CloudDocs"
[ -d "$ICLOUD" ] && scan --surface icloud-drive --root "$ICLOUD"

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
