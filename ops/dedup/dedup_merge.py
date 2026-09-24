#!/usr/bin/env python3
"""dedup_merge.py — phase 2: combine every surface's inventory, find duplicates, write a keep/archive PLAN.

    python3 dedup_merge.py --in <dir> --prefer mac-local --prefer gdrive-powerconnection [--workers 8]

Only files whose size collides with another file are hashed (sha256), and only if they are local.
Cloud-only placeholders are never opened; they can still be matched by name + size as "probable" duplicates.
Outputs in <dir>:
  duplicates.csv        group, sha256, size, action (keep|archive|flag-legal), surface, path
  near-duplicates.csv   same normalized name ("copy", "(1)", "-v2", "final", dates stripped), different content
  cloud-probable.csv    cloud-only placeholder whose name + size match a local file (verify before acting)
  PLAN.md               per-surface totals and reclaimable bytes
Keeper per group: first --prefer surface present, then shortest path, then oldest mtime.
Legal-flagged files are never planned for archive; groups containing them are reported as flag-legal.
"""
import argparse, csv, glob, hashlib, os, re
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

NOISE = re.compile(r"(\s*\(\d+\)|[ _-]*copy( \d+)?|[ _-]*v\d+|[ _-]*final|[ _-]*\d{4}[-_.]?\d{2}[-_.]?\d{2}(t\d+z?)?|[ _-]*\d{6,})$", re.I)


def sha256(path):
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return ""


def norm_name(path):
    stem, ext = os.path.splitext(os.path.basename(path))
    prev = None
    while prev != stem:
        prev, stem = stem, NOISE.sub("", stem).strip()
    return stem.lower() + ext.lower()


def human(n):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--in", dest="indir", required=True, type=Path)
    ap.add_argument("--prefer", action="append", default=[], help="surface order for keepers (repeatable)")
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()

    rows = []
    for inv in sorted(glob.glob(str(a.indir / "inventory-*.csv"))):
        with open(inv, newline="") as f:
            for r in csv.DictReader(f):
                r["size"], r["mtime"] = int(r["size"]), int(r["mtime"])
                r["local"], r["legal"] = r["local"] == "1", r["legal"] == "1"
                rows.append(r)

    by_size = defaultdict(list)
    for r in rows:
        by_size[r["size"]].append(r)
    to_hash = [r for group in by_size.values() if len(group) > 1 for r in group if r["local"]]
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        for r, h in zip(to_hash, ex.map(lambda r: sha256(r["path"]), to_hash)):
            r["sha256"] = h

    rank = {s: i for i, s in enumerate(a.prefer)}
    groups = defaultdict(list)
    for r in to_hash:
        if r.get("sha256"):
            groups[r["sha256"]].append(r)
    groups = {h: g for h, g in groups.items() if len(g) > 1}

    reclaim = defaultdict(int)
    with open(a.indir / "duplicates.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["group", "sha256", "size", "action", "surface", "path"])
        for gi, (h, g) in enumerate(sorted(groups.items(), key=lambda kv: -kv[1][0]["size"] * len(kv[1])), 1):
            g.sort(key=lambda r: (rank.get(r["surface"], len(rank)), len(r["path"]), r["mtime"]))
            keeper = g[0]
            legal = any(r["legal"] for r in g)
            for r in g:
                if r is keeper:
                    action = "keep"
                elif legal or r["legal"]:
                    action = "flag-legal"
                else:
                    action = "archive"
                    reclaim[r["surface"]] += r["size"]
                w.writerow([gi, h, r["size"], action, r["surface"], r["path"]])

    by_norm = defaultdict(list)
    for r in rows:
        by_norm[norm_name(r["path"])].append(r)
    with open(a.indir / "near-duplicates.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["normalized_name", "surface", "size", "mtime", "legal", "path"])
        for key, g in sorted(by_norm.items()):
            hashes = {r.get("sha256") or f"size:{r['size']}" for r in g}
            if len(g) > 1 and len(hashes) > 1:
                for r in sorted(g, key=lambda r: -r["mtime"]):
                    w.writerow([key, r["surface"], r["size"], r["mtime"], int(r["legal"]), r["path"]])

    local_index = {(os.path.basename(r["path"]).lower(), r["size"]) for r in rows if r["local"]}
    with open(a.indir / "cloud-probable.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["surface", "size", "path"])
        for r in rows:
            name = os.path.basename(r["path"])
            if not r["local"]:
                real = name[1:-len(".icloud")] if name.startswith(".") and name.endswith(".icloud") else name
                if (real.lower(), r["size"]) in local_index:
                    w.writerow([r["surface"], r["size"], r["path"]])

    surfaces = sorted({r["surface"] for r in rows})
    lines = ["# Dedup plan (dry run: nothing has moved)", "",
             f"{len(rows)} files scanned across {len(surfaces)} surfaces · {len(to_hash)} hashed (size collisions, local only) · "
             f"{len(groups)} exact-duplicate groups", "", "| Surface | Files | Cloud-only | Legal-flagged | Reclaimable (archive) |", "|---|---|---|---|---|"]
    for s in surfaces:
        sr = [r for r in rows if r["surface"] == s]
        lines.append(f"| {s} | {len(sr)} | {sum(not r['local'] for r in sr)} | {sum(r['legal'] for r in sr)} | {human(reclaim[s])} |")
    lines += ["", f"**Total reclaimable:** {human(sum(reclaim.values()))}", "",
              "Review `duplicates.csv` (action=archive rows), `near-duplicates.csv` (manual review), `cloud-probable.csv` (verify).",
              "Legal-flagged groups are marked `flag-legal` and will not be moved.", "",
              "Apply (after approval): `python3 ops/dedup/dedup_apply.py --plan <dir>/duplicates.csv --archive-root /Volumes/<SSD>/Dedup-Archive --apply`"]
    (a.indir / "PLAN.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines[:3] + [f"  reclaimable: {human(sum(reclaim.values()))} → {a.indir / 'PLAN.md'}"]))


if __name__ == "__main__":
    main()
