# Dedup across every surface (Mac + cloud folders + iCloud): dry run first

**Beginner? Run just this** (plug in your external SSD first). It checks your setup, asks which drive to use, scans, and shows the report. Nothing moves:
```bash
cd ~/Code/connectedagents-ai/repo-template && git pull
bash ops/dedup/start_here.sh
```

```bash
OUT=/Volumes/<ExternalSSD>/dedup-runs bash ops/dedup/run_dedup.sh     # parallel scan per surface → merge → PLAN.md
python3 ops/dedup/dedup_apply.py --plan <run>/duplicates.csv --archive-root /Volumes/<ExternalSSD>/Dedup-Archive          # dry run
python3 ops/dedup/dedup_apply.py --plan <run>/duplicates.csv --archive-root /Volumes/<ExternalSSD>/Dedup-Archive --apply  # after approval
```

| Phase | Script | Notes |
|---|---|---|
| Scan (parallel, one per surface) | `dedup_scan.py` | metadata only. Surfaces: `mac-local` (Desktop, Documents, Downloads, ~/Code), each `~/Library/CloudStorage/*` (Google Drive, OneDrive, Dropbox, Box), `icloud-drive`. Skips node_modules, .venv, build caches, app bundles and Photos libraries |
| Scan one document folder | `dedup_scan.py --root <folder> --ext pdf --ext xlsx … --skip-repos` | `--ext` keeps only those file types; `--skip-repos` skips whole git repos (tracked source too), so a folder full of clones is safe to scan |
| Merge | `dedup_merge.py` | hashes **only** files whose size collides, and only local ones. Groups exact duplicates across surfaces, picks a keeper (preferred surface → shortest path → oldest), and lists near-duplicates (copy, (1), -v2, final, dates) for manual review |
| Apply | `dedup_apply.py` | moves `archive` rows to an **external** volume, re-checking hashes first. Writes MANIFEST.tsv + restore.sh. Never deletes |
| Cloud accounts (optional) | `connect_cloud.sh` → `cloud_inventory.py` → `cloud_apply.py` | Google Drive (one remote per Google login), OneDrive (per Microsoft account/tenant), SharePoint (one remote per site library) and pCloud, listed through their APIs with **rclone**. Uses the checksums the provider already stores, so **nothing is downloaded**. Cloud files match each other and your local files exactly. `cloud_apply.py` moves duplicates into `_Dedup-Archive/` inside the same account (server-side, undo script, never deletes) and only when the keeper is in that same account |

**One external SSD with jdupes** (fast, read-only report): `jdupes -r -j -q "$SSD" > jdupes.json`, then `jdupes_archive.py --json jdupes.json --root "$SSD" --archive "$SSD/_Dedup-Archive/<stamp>" --out <run>` (dry run, writes plan.csv), then `--apply`. Keeper = shortest path, legal-looking sets are never moved, every copy is re-checked byte-for-byte, moves are undone with `restore.sh`.

**Find where files are now** (after folders moved or a collapse): `locate_by_hash.py --hashes <list.csv> --root ~ --root <archive> --out <dir>`.
Read-only. Takes a list of fingerprints (SHA-256, SHA-1, MD5 or OneDrive QuickXor, detected automatically; add `size` and `old_path` columns
when you have them, which makes it much faster) and writes `located.csv` (old path → current path, every copy) and `missing.csv`.

**Consolidate into one master folder** (after the dedup): `consolidate_to_drive.py --root <folder> --ext … --dest "<remote>:<master folder>" --archive-root <dir> [--plan <run>/duplicates.csv]`
(dry run), then `--apply`. Each file is copied with `rclone copyto --checksum`, its checksum is re-read from the cloud, and only verified files have
the local original moved to the archive root (never deleted, never overwriting a different cloud file). `--plan` leaves out the copies the dedup
planned to archive. Needs a writable remote: `rclone config update <remote> scope=drive`.

**OneDrive / SharePoint:** Microsoft stores a QuickXorHash for every file; `quickxorhash.py` computes the same value for local files
(checked against rclone's own output), so OneDrive ↔ SharePoint ↔ Mac copies match exactly without downloading. Scan one SharePoint
library at a time if a site is large: `python3 ops/dedup/cloud_inventory.py --remote "sp-legalmatters:Shared Documents" --out <run>`
(then re-run `dedup_merge.py --in <run>`). `CLOUD_REMOTES` itself is space-separated, so list whole remotes there (`sp-legalmatters:`). Legal-looking paths are flagged and never moved.

**Google Drive, OneDrive/SharePoint and pCloud:** run `bash ops/dedup/connect_cloud.sh` once (it installs rclone if you agree, then opens a browser to sign in;
Google is connected read-only). `start_here.sh` then offers to include those accounts. When a Google Drive account is listed through the API,
the `~/Library/CloudStorage/GoogleDrive-*` folders are not scanned as well, so no file is compared with itself. pCloud's virtual drive is never walked:
reading it would download the files. Google Docs/Sheets/Slides and Drive shortcuts are skipped (no checksum / not real copies).
Archiving inside Google Drive needs write access later: `rclone config update gdrive-<label> scope=drive` (the script tells you when).

**iCloud rules:** cloud-only files (not downloaded) are never opened, so no downloads are triggered. They can only appear as "probable" name+size matches
(`cloud-probable.csv`). iCloud files are skipped by apply unless `--include-icloud`, because moving a file out of iCloud Drive removes it from every device.
**Photos:** use Photos → Utilities → Duplicates (built into macOS). The Photos library is never scanned by these scripts.
**Legal hold:** paths matching the legal pattern (Tesla, Connected Solar, NetZero, Dorellyn Lee, Mullins, litigation, court, privileged, …) are flagged
`flag-legal`, and nothing in their group is ever planned for archive. Adjust with `--legal-pattern` in `dedup_scan.py`.
**Disk space:** set `OUT=` to the external SSD so reports don't use the internal disk. The archive root must be on `/Volumes/...` unless `--allow-internal`.

Running it as an agent swarm: in the Claude Code session **on the Mac**, ask for a workflow where one agent per surface runs `dedup_scan.py`,
one merges with `dedup_merge.py`, and you review `PLAN.md` before any `dedup_apply.py --apply`. `run_dedup.sh` does the same with parallel processes.
