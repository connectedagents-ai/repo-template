#!/bin/bash
# ssd_dedup.sh — find exact duplicate files ON THE SSD and preview deleting the extra copies, to free space.
#
#   bash ops/dedup/ssd_dedup.sh                          # uses "/Volumes/Extreme SSD"
#   bash ops/dedup/ssd_dedup.sh "/Volumes/Other Drive"
#
# Reads the drive in place (nothing is copied to the Mac), writes a small report on the drive itself, and ends with a
# PREVIEW of what would be deleted. It deletes nothing: the last line prints the command that does, for after you look.
# Keeps the clean name ("Report.pdf" over "Report (1).pdf"); legal-flagged files are never deleted.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
SSD="${1:-/Volumes/Extreme SSD}"
if [ ! -d "$SSD" ]; then
  echo "Drive not found: $SSD"
  echo "Connected drives:"; ls /Volumes 2>/dev/null | sed 's/^/  /'
  echo "Run again with the drive's name, e.g.:  bash ops/dedup/ssd_dedup.sh \"/Volumes/<name>\""
  exit 1
fi
RUN="$SSD/dedup-runs/ssd-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$RUN" || { echo "Cannot write to $SSD (is it read-only or full?)"; exit 1; }
echo "Free on the drive before: $(df -h "$SSD" | awk 'NR==2 {print $4}')"
echo "1/3 Listing files on $SSD (read-only)…"
python3 "$HERE/dedup_scan.py" --surface ssd --root "$SSD" --out "$RUN" || exit 1
echo "2/3 Comparing contents of same-size files (read in place)…"
python3 "$HERE/dedup_merge.py" --in "$RUN" --prefer ssd >/dev/null || exit 1
echo "3/3 Preview:"
python3 "$HERE/delete_exact_duplicates.py" --plan "$RUN/duplicates.csv" | tail -25
echo
echo "Full list: $RUN/duplicates.csv   ·   Different versions to review by hand: $RUN/near-duplicates.csv"
echo "To delete the duplicates listed above, run:"
echo "  python3 \"$HERE/delete_exact_duplicates.py\" --plan \"$RUN/duplicates.csv\" --apply"
