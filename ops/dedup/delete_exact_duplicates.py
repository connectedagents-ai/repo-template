#!/usr/bin/env python3
"""delete_exact_duplicates.py — free space on an external drive by deleting EXACT duplicate files. DRY RUN by default.

    python3 delete_exact_duplicates.py --plan "/Volumes/Extreme SSD/dedup-runs/ssd-<stamp>/duplicates.csv"          # preview
    python3 delete_exact_duplicates.py --plan "/Volumes/Extreme SSD/dedup-runs/ssd-<stamp>/duplicates.csv" --apply  # delete

Use this when the archive would sit on the same drive (moving there frees nothing). Every deletion is guarded:
- only action=archive rows from dedup_merge.py (the kept copy prefers the clean name; legal-flagged groups never appear);
- only files on an external volume (/Volumes/...), never the Mac's internal disk;
- the kept copy must still exist on the SAME volume, and both files are re-hashed right before deleting: both must
  match the plan's sha256, so a file that changed since the scan is left alone;
- writes DELETED.tsv and restore.sh next to the plan: restore.sh re-creates every deleted file from its kept copy.
"""
import argparse, csv, hashlib, os, shlex, sys
from collections import Counter
from pathlib import Path


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def check(row, keeper, allow_internal=False):
    """None if the file may be deleted, else the reason to leave it."""
    src, digest = row["path"], row.get("sha256", "")
    if not src.startswith("/Volumes/") and not allow_internal:
        return "not on an external drive"
    if not digest:
        return "no sha256 in plan"
    if not keeper or not os.path.isfile(keeper):
        return "kept copy missing"
    if not os.path.isfile(src):
        return "already gone"
    s, k = os.stat(src), os.stat(keeper)
    if s.st_dev != k.st_dev:
        return "kept copy is on another drive"
    if s.st_ino == k.st_ino or os.path.realpath(src) == os.path.realpath(keeper):
        return "same file as the kept copy"
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plan", required=True, type=Path, help="duplicates.csv from dedup_merge.py")
    ap.add_argument("--apply", action="store_true", help="really delete (default: preview only)")
    ap.add_argument("--allow-internal", action="store_true", help="also allow files outside /Volumes (not recommended)")
    a = ap.parse_args()

    rows = list(csv.DictReader(open(a.plan, newline="")))
    keepers = {r["group"]: r["path"] for r in rows if r["action"] == "keep"}
    skipped, freed, done = Counter(), 0, 0
    log = restore = None
    if a.apply:
        log = open(a.plan.parent / "DELETED.tsv", "a")
        new = not (a.plan.parent / "restore.sh").exists()
        restore = open(a.plan.parent / "restore.sh", "a")
        if new:
            restore.write("#!/bin/bash\n# Re-create files deleted by delete_exact_duplicates.py from their kept copies\n")
    try:
        for r in (r for r in rows if r["action"] == "archive"):
            keeper = keepers.get(r["group"], "")
            why = check(r, keeper, a.allow_internal)
            if why:
                skipped[why] += 1
                continue
            if not a.apply:
                print(f"would delete  {r['path']}\n      kept:  {keeper}")
                freed += int(r["size"])
                done += 1
                continue
            if sha256(r["path"]) != r["sha256"] or sha256(keeper) != r["sha256"]:
                skipped["changed since the scan"] += 1
                continue
            try:
                os.remove(r["path"])
            except OSError as e:
                print(f"  could not delete {r['path']}: {e}", file=sys.stderr)
                skipped["error"] += 1
                continue
            log.write(f"{r['sha256']}\t{r['size']}\t{r['path']}\t{keeper}\n")
            restore.write(f"mkdir -p {shlex.quote(os.path.dirname(r['path']))} && "
                          f"cp -p {shlex.quote(keeper)} {shlex.quote(r['path'])}\n")
            log.flush(); restore.flush()
            freed += int(r["size"])
            done += 1
    finally:
        if a.apply:
            log.close(); restore.close()
            os.chmod(a.plan.parent / "restore.sh", 0o755)
    verb = "Deleted" if a.apply else "Would delete"
    print(f"\n{verb} {done} duplicate files, freeing {freed / 1e9:.2f} GB. Left alone: {sum(skipped.values())} {dict(skipped) or ''}")
    print(f"Undo: bash {shlex.quote(str(a.plan.parent / 'restore.sh'))}" if a.apply
          else "Preview only: nothing was deleted. Re-run with --apply to delete.")


if __name__ == "__main__":
    main()
