#!/usr/bin/env python3
"""dedup_apply.py — phase 3 (only after the owner approves PLAN.md): move action=archive files to an archive root.

    python3 dedup_apply.py --plan <dir>/duplicates.csv --archive-root /Volumes/ExtremeSSD/Dedup-Archive          # DRY RUN
    python3 dedup_apply.py --plan <dir>/duplicates.csv --archive-root /Volumes/ExtremeSSD/Dedup-Archive --apply

Safety:
- DRY RUN by default. Never deletes; moves preserve the original path under <archive-root>/<stamp>/.
- Archive root must be on an external volume (/Volumes/...) unless --allow-internal.
- Before each move, the file's sha256 is re-checked against the plan and the group's keeper must still exist.
- action=flag-legal and action=keep rows are never touched.
- Files under iCloud Drive are skipped unless --include-icloud, and files in ~/Library/CloudStorage (Google Drive,
  OneDrive, Dropbox, Box) unless --include-cloud-sync: moving them out of a synced folder deletes them from the cloud.
- Writes MANIFEST.tsv and restore.sh (shell-quoted paths) into the run folder, one line per completed move, flushed
  as it goes. A move that fails is reported and skipped; the rest of the run continues.
"""
import argparse, csv, datetime, hashlib, os, shlex, shutil, sys
from collections import defaultdict
from pathlib import Path

ICLOUD = "/Library/Mobile Documents/"
CLOUD_SYNC = "/Library/CloudStorage/"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plan", required=True, type=Path)
    ap.add_argument("--archive-root", required=True, type=Path)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--allow-internal", action="store_true")
    ap.add_argument("--include-icloud", action="store_true")
    ap.add_argument("--include-cloud-sync", action="store_true", help="also move files inside ~/Library/CloudStorage")
    a = ap.parse_args()

    root = a.archive_root.expanduser().resolve()
    if not str(root).startswith("/Volumes/") and not a.allow_internal:
        sys.exit(f"refusing: {root} is not on an external volume (/Volumes/...). Use --allow-internal to override.")
    if a.apply and not root.parent.exists():
        sys.exit(f"archive volume not mounted: {root.parent}")

    rows = list(csv.DictReader(open(a.plan, newline="")))
    keepers = {r["group"]: r["path"] for r in rows if r["action"] == "keep"}
    run = root / datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    moved = skipped = 0
    total = 0
    manifest = restore = None
    if a.apply:
        run.mkdir(parents=True, exist_ok=True)
        manifest = open(run / "MANIFEST.tsv", "w")
        manifest.write("group\tsha256\tsize\tfrom\tto\n")
        restore = open(run / "restore.sh", "w")
        restore.write("#!/bin/bash\n# Undo dedup_apply run\nset -e\n")
    reasons = defaultdict(int)
    try:
        for r in (r for r in rows if r["action"] == "archive"):
            m, why = archive_one(r, keepers, run, a)
            if why:
                reasons[why] += 1
                skipped += 1
                continue
            total += int(r["size"])
            if m:
                src, dst = m
                manifest.write(f"{r['group']}\t{r['sha256']}\t{r['size']}\t{src}\t{dst}\n")
                restore.write(f"mkdir -p {shlex.quote(os.path.dirname(src))} && mv {shlex.quote(str(dst))} {shlex.quote(src)}\n")
                manifest.flush(); restore.flush()
                moved += 1
    finally:
        if a.apply:
            manifest.close(); restore.close(); os.chmod(run / "restore.sh", 0o755)
    print(f"\n{'moved' if a.apply else 'would move'}: {moved if a.apply else sum(1 for r in rows if r['action']=='archive') - skipped} files "
          f"({total / 1e9:.2f} GB) · skipped: {skipped} {dict(reasons) if reasons else ''}")
    print(f"Undo: bash {shlex.quote(str(run / 'restore.sh'))}" if a.apply else "Dry run. Re-run with --apply after approval.")


def archive_one(r, keepers, run, a):
    """Returns ((src, dst) or None, skip reason or None). Never raises for a single file's problem."""
    src = r["path"]
    if ICLOUD in src and not a.include_icloud:
        return None, "icloud (needs --include-icloud)"
    if CLOUD_SYNC in src and not a.include_cloud_sync:
        return None, "cloud-sync folder (needs --include-cloud-sync)"
    if not os.path.isfile(src):
        return None, "missing"
    if not os.path.isfile(keepers.get(r["group"], "")):
        return None, "keeper missing"
    dst = run / src.lstrip("/")
    print(f"{'move' if a.apply else 'would move'}  {src}  →  {dst}")
    if not a.apply:
        return None, None
    try:
        if sha256(src) != r["sha256"] or sha256(keepers[r["group"]]) != r["sha256"]:
            return None, "changed since scan"
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(src, dst)
    except OSError as e:
        print(f"  ✗ could not move {src}: {e}", file=sys.stderr)
        if os.path.isfile(src) and dst.exists():  # partial copy across volumes: original is intact, drop the fragment
            dst.unlink()
        return None, "error"
    return (src, dst), None


if __name__ == "__main__":
    main()
