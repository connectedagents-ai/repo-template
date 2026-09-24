#!/usr/bin/env python3
"""cloud_apply.py — archive duplicate files INSIDE a cloud account (Google Drive, pCloud, …) without downloading them.

    python3 cloud_apply.py --plan <run>/duplicates.csv            # DRY RUN: lists what would move
    python3 cloud_apply.py --plan <run>/duplicates.csv --apply    # only after you approve the plan

Safety:
- DRY RUN by default. Never deletes: each duplicate is moved (server-side, `rclone moveto`) into
  <remote>:_Dedup-Archive/<stamp>/<original path> in the SAME account, so it stays recoverable and nothing is downloaded.
- Only acts when the group's keeper is in the same account (a copy that exists only elsewhere is never archived away),
  unless --allow-cross-surface.
- Before each move the file is re-listed and its provider checksum must still match the plan.
- flag-legal and keep rows are never touched. Writes MANIFEST.tsv and restore.sh (undo) into ./cloud-dedup-<stamp>/.
- Google Drive remotes created read-only (connect_cloud.sh default) can't move files: the script tells you how to
  allow it when you're ready.
"""
import argparse, csv, datetime, json, os, re, shlex, subprocess, sys
from collections import defaultdict
from pathlib import Path

REMOTE = re.compile(r"^([A-Za-z0-9._ -]+):(.+)$")


def split_remote(path):
    m = REMOTE.match(path)
    return (m.group(1), m.group(2)) if m and not path.startswith("/") else (None, None)


def current_hashes(path):
    r = subprocess.run(["rclone", "lsjson", "--hash", "--files-only", path], capture_output=True, text=True)
    if r.returncode != 0:
        return None
    items = json.loads(r.stdout or "[]")
    return {f"{t}:{v}" for t, v in (items[0].get("Hashes") or {}).items() if v} if items else None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plan", required=True, type=Path)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--archive-folder", default="_Dedup-Archive")
    ap.add_argument("--allow-cross-surface", action="store_true", help="also archive when the keeper is in another account or on the Mac")
    ap.add_argument("--out", type=Path, default=Path.cwd())
    a = ap.parse_args()
    with open(a.plan, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    keepers = {r["group"]: r["path"] for r in rows if r["action"] == "keep"}
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    run = a.out / f"cloud-dedup-{stamp}"
    reasons, moved, total = defaultdict(int), 0, 0
    manifest = restore = None
    if a.apply:
        run.mkdir(parents=True, exist_ok=True)
        manifest = open(run / "MANIFEST.tsv", "w", encoding="utf-8")
        manifest.write("group\tsize\tfrom\tto\n")
        restore = open(run / "restore.sh", "w", encoding="utf-8")
        restore.write("#!/bin/bash\n# Undo cloud_apply run: moves each file back to where it was\nset -e\n")
    try:
        for r in (r for r in rows if r["action"] == "archive"):
            remote, rel = split_remote(r["path"])
            if not remote:
                continue  # local files are dedup_apply.py's job
            k_remote, _ = split_remote(keepers.get(r["group"], ""))
            if k_remote != remote and not a.allow_cross_surface:
                reasons["keeper not in the same account"] += 1
                continue
            dst = f"{remote}:{a.archive_folder}/{stamp}/{rel}"
            print(f"{'move' if a.apply else 'would move'}  {r['path']}  →  {dst}")
            if not a.apply:
                moved += 1
                total += int(r["size"])
                continue
            now = current_hashes(r["path"])
            planned = {h for h in (r.get("hashes") or "").split(";") if h}
            if not now or not (now & planned):
                reasons["missing or changed since scan"] += 1
                continue
            res = subprocess.run(["rclone", "moveto", r["path"], dst], capture_output=True, text=True)
            if res.returncode != 0:
                reasons["error"] += 1
                msg = res.stderr.strip().splitlines()[-1:] or ["unknown error"]
                print(f"  ✗ {msg[0]}", file=sys.stderr)
                if "insufficient" in res.stderr.lower() or "403" in res.stderr:
                    print(f"  → this account was connected read-only. When you're ready: rclone config update {remote} scope=drive", file=sys.stderr)
                continue
            manifest.write(f"{r['group']}\t{r['size']}\t{r['path']}\t{dst}\n")
            restore.write(f"rclone moveto {shlex.quote(dst)} {shlex.quote(r['path'])}\n")
            manifest.flush(); restore.flush()
            moved += 1
            total += int(r["size"])
    finally:
        if a.apply:
            manifest.close(); restore.close(); os.chmod(run / "restore.sh", 0o755)
    print(f"\n{'moved' if a.apply else 'would move'}: {moved} cloud files ({total / 1e9:.2f} GB) · skipped: {dict(reasons) or 0}")
    print(f"Undo: bash {shlex.quote(str(run / 'restore.sh'))}" if a.apply else "Dry run. Re-run with --apply after approval.")


if __name__ == "__main__":
    main()
