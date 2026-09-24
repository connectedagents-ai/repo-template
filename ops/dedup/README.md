# Dedup across every surface (Mac + cloud folders + iCloud): dry run first

```bash
OUT=/Volumes/<ExternalSSD>/dedup-runs bash ops/dedup/run_dedup.sh     # parallel scan per surface → merge → PLAN.md
python3 ops/dedup/dedup_apply.py --plan <run>/duplicates.csv --archive-root /Volumes/<ExternalSSD>/Dedup-Archive          # dry run
python3 ops/dedup/dedup_apply.py --plan <run>/duplicates.csv --archive-root /Volumes/<ExternalSSD>/Dedup-Archive --apply  # after approval
```

| Phase | Script | Notes |
|---|---|---|
| Scan (parallel, one per surface) | `dedup_scan.py` | metadata only. Surfaces: `mac-local` (Desktop, Documents, Downloads, ~/Code), each `~/Library/CloudStorage/*` (Google Drive, OneDrive, Dropbox, Box), `icloud-drive`. Skips node_modules, .venv, build caches, app bundles and Photos libraries |
| Merge | `dedup_merge.py` | hashes **only** files whose size collides, and only local ones. Groups exact duplicates across surfaces, picks a keeper (preferred surface → shortest path → oldest), and lists near-duplicates (copy, (1), -v2, final, dates) for manual review |
| Apply | `dedup_apply.py` | moves `archive` rows to an **external** volume, re-checking hashes first. Writes MANIFEST.tsv + restore.sh. Never deletes |

**iCloud rules:** cloud-only files (not downloaded) are never opened, so no downloads are triggered. They can only appear as "probable" name+size matches
(`cloud-probable.csv`). iCloud files are skipped by apply unless `--include-icloud`, because moving a file out of iCloud Drive removes it from every device.
**Photos:** use Photos → Utilities → Duplicates (built into macOS). The Photos library is never scanned by these scripts.
**Legal hold:** paths matching the legal pattern (Tesla, Connected Solar, NetZero, Dorellyn Lee, Mullins, litigation, court, privileged, …) are flagged
`flag-legal`, and nothing in their group is ever planned for archive. Adjust with `--legal-pattern` in `dedup_scan.py`.
**Disk space:** set `OUT=` to the external SSD so reports don't use the internal disk. The archive root must be on `/Volumes/...` unless `--allow-internal`.

Running it as an agent swarm: in the Claude Code session **on the Mac**, ask for a workflow where one agent per surface runs `dedup_scan.py`,
one merges with `dedup_merge.py`, and you review `PLAN.md` before any `dedup_apply.py --apply`. `run_dedup.sh` does the same with parallel processes.
