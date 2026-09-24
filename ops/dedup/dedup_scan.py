#!/usr/bin/env python3
"""dedup_scan.py — phase 1 (one per surface, run in parallel): READ-ONLY metadata inventory.

    python3 dedup_scan.py --surface mac-local --root ~/Desktop --root ~/Documents --out <dir>
    python3 dedup_scan.py --surface icloud-drive --root "~/Library/Mobile Documents/com~apple~CloudDocs" --out <dir>

Writes <dir>/inventory-<surface>.csv: surface, path, size, mtime, local (0/1), legal (0/1).
Never reads file contents here (hashing happens only in dedup_merge.py, and only for size collisions).
iCloud-safe: files that are not downloaded (macOS "dataless" flag, or old-style .<name>.icloud placeholders)
are recorded with local=0 and are never opened, so no download is ever triggered.
Legal-looking paths are flagged legal=1; later phases never plan to move them.
"""
import argparse, csv, os, re, stat, sys
from pathlib import Path

SF_DATALESS = 0x40000000  # macOS: file content is not on disk (cloud placeholder)
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", ".next", "dist", "build", ".turbo", ".cache",
             ".Trash", ".Trashes", ".DocumentRevisions-V100", ".Spotlight-V100", ".fseventsd", ".TemporaryItems",
             "dedup-runs", "Dedup-Archive"}
SKIP_SUFFIXES = (".app", ".photoslibrary", ".musiclibrary", ".tvlibrary", ".bundle", ".framework", ".xcarchive")
DEFAULT_LEGAL = (r"tesla|connected[ _-]?solar|netzero|net[ _-]?zero|dorellyn|mullins|abad|vikta|blair|litigat|lawsuit|"
                 r"court|legal|privileged|deposition|subpoena|discovery[ _-]?production|evidence|golden[ _-]?packet")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--surface", required=True, help="label, e.g. mac-local, gdrive-powerconnection, onedrive-onewishlabs, icloud-drive")
    ap.add_argument("--root", action="append", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--legal-pattern", default=DEFAULT_LEGAL, help="regex; matching paths are flagged and never moved")
    ap.add_argument("--min-size", type=int, default=1, help="ignore files smaller than this many bytes")
    a = ap.parse_args()
    legal = re.compile(a.legal_pattern, re.I)
    a.out.mkdir(parents=True, exist_ok=True)
    out = a.out / f"inventory-{re.sub(r'[^A-Za-z0-9._-]', '_', a.surface)}.csv"
    n = local = placeholders = flagged = errors = 0
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["surface", "path", "size", "mtime", "local", "legal"])
        for root in a.root:
            root = root.expanduser()
            if not root.exists():
                print(f"  skip missing root {root}", file=sys.stderr)
                continue
            root_dev = os.stat(root).st_dev
            for dirpath, dirnames, filenames in os.walk(root, onerror=lambda e: None):  # does not follow symlinks
                dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.endswith(SKIP_SUFFIXES)
                               and os.lstat(os.path.join(dirpath, d)).st_dev == root_dev]  # stay on this volume
                for name in filenames:
                    if name == ".DS_Store":
                        continue
                    p = os.path.join(dirpath, name)
                    try:
                        st = os.lstat(p)
                    except OSError:
                        errors += 1
                        continue
                    if not stat.S_ISREG(st.st_mode):
                        continue
                    is_placeholder = name.startswith(".") and name.endswith(".icloud")
                    is_local = not is_placeholder and not (getattr(st, "st_flags", 0) & SF_DATALESS)
                    if st.st_size < a.min_size and is_local:
                        continue
                    is_legal = bool(legal.search(p))
                    w.writerow([a.surface, p, st.st_size, int(st.st_mtime), int(is_local), int(is_legal)])
                    n += 1
                    local += is_local
                    placeholders += not is_local
                    flagged += is_legal
    print(f"  {a.surface}: {n} files ({local} local, {placeholders} cloud-only placeholders, {flagged} legal-flagged, {errors} unreadable) → {out}")


if __name__ == "__main__":
    main()
