#!/usr/bin/env python3
"""dedup_merge.py — phase 2: combine every surface's inventory, find duplicates, write a keep/archive PLAN.

    python3 dedup_merge.py --in <dir> --prefer mac-local --prefer gdrive-powerconnection [--workers 8]

Only files whose size collides with another file are hashed (sha256), and only if they are local.
Cloud-only placeholders are never opened; they can still be matched by name + size as "probable" duplicates.
Cloud-account inventories (cloud_inventory.py) carry the provider's own checksums (md5/sha1/sha256, OneDrive quickxor): cloud files are
matched on those without downloading, and a local file that collides in size with one is also hashed with that
algorithm so local ↔ cloud copies are matched exactly.
Outputs in <dir>:
  duplicates.csv        group, sha256, size, action (keep|archive|flag-legal), surface, path, hashes
  near-duplicates.csv   same normalized name ("copy", "(1)", "-v2", "final", dates stripped), different content
  cloud-probable.csv    cloud-only placeholder whose name + size match a local file (verify before acting)
  PLAN.md               per-surface totals and reclaimable bytes
Keeper per group: first --prefer surface present, then shortest path, then oldest mtime.
Legal-flagged files are never planned for archive; groups containing them are reported as flag-legal.
"""
import argparse, csv, glob, hashlib, os, re, sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from quickxorhash import QuickXorHash  # noqa: E402  (OneDrive / SharePoint checksum)

NOISE = re.compile(r"(\s*\(\d+\)|[ _-]*copy( \d+)?|[ _-]*v\d+|[ _-]*final|[ _-]*\d{4}[-_.]?\d{2}[-_.]?\d{2}(t\d+z?)?|[ _-]*\d{6,})$", re.I)


HASHERS = {"sha256": hashlib.sha256, "sha1": hashlib.sha1, "md5": hashlib.md5, "quickxor": QuickXorHash}


def file_hashes(path, types=("sha256",)):
    """One read, several digests. {} if unreadable."""
    hs = {t: HASHERS[t]() for t in types if t in HASHERS}
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                for h in hs.values():
                    h.update(chunk)
        return {t: h.hexdigest() for t, h in hs.items()}
    except OSError:
        return {}


def parse_hashes(text):
    return dict(p.split(":", 1) for p in (text or "").split(";") if ":" in p)


def find(parent, i):
    while parent[i] != i:
        parent[i] = parent[parent[i]]
        i = parent[i]
    return i


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
                r["hashes"] = parse_hashes(r.get("hashes"))  # provider checksums (cloud inventories only)
                rows.append(r)

    by_size = defaultdict(list)
    for r in rows:
        by_size[r["size"]].append(r)
    jobs = []  # (row, digest types): local files whose size collides, hashed with sha256 + any cloud algorithm in play
    for group in (g for g in by_size.values() if len(g) > 1):
        types = {"sha256"} | {t for r in group for t in r["hashes"]}
        jobs += [(r, tuple(sorted(types))) for r in group if r["local"]]
    to_hash = [r for r, _ in jobs]
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        for (r, _), hs in zip(jobs, ex.map(lambda j: file_hashes(j[0]["path"], j[1]), jobs)):
            r["hashes"].update(hs)
            r["sha256"] = hs.get("sha256", "")

    # rows sharing any checksum (same algorithm) are one group, e.g. local sha256+md5 ↔ Drive md5 ↔ pCloud md5/sha1
    cand = [r for g in by_size.values() if len(g) > 1 for r in g if r["hashes"]]
    parent = list(range(len(cand)))
    first = {}
    for i, r in enumerate(cand):
        for key in (f"{t}:{v}" for t, v in r["hashes"].items()):
            if key in first:
                parent[find(parent, i)] = find(parent, first[key])
            else:
                first[key] = i
    by_root = defaultdict(list)
    for i, r in enumerate(cand):
        by_root[find(parent, i)].append(r)
    groups = {}
    for g in (g for g in by_root.values() if len(g) > 1):
        local_sha = next((r["sha256"] for r in g if r.get("sha256")), "")
        key = local_sha or next(f"{t}:{v}" for t, v in sorted(g[0]["hashes"].items()))
        groups[key] = g
        for r in g:
            r["group_key"] = key

    rank = {s: i for i, s in enumerate(a.prefer)}

    reclaim = defaultdict(int)
    with open(a.indir / "duplicates.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["group", "sha256", "size", "action", "surface", "path", "hashes"])
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
                w.writerow([gi, h, r["size"], action, r["surface"], r["path"],
                            ";".join(f"{t}:{v}" for t, v in sorted(r["hashes"].items()))])

    by_norm = defaultdict(list)
    for r in rows:
        by_norm[norm_name(r["path"])].append(r)
    with open(a.indir / "near-duplicates.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["normalized_name", "surface", "size", "mtime", "legal", "path"])
        for key, g in sorted(by_norm.items()):
            hashes = {r.get("group_key") or r.get("sha256") or f"size:{r['size']}" for r in g}
            if len(g) > 1 and len(hashes) > 1:
                for r in sorted(g, key=lambda r: -r["mtime"]):
                    w.writerow([key, r["surface"], r["size"], r["mtime"], int(r["legal"]), r["path"]])

    local_index = {(os.path.basename(r["path"]).lower(), r["size"]) for r in rows if r["local"]}
    with open(a.indir / "cloud-probable.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["surface", "size", "path"])
        for r in rows:
            name = os.path.basename(r["path"])
            if not r["local"] and not r.get("group_key"):
                real = name[1:-len(".icloud")] if name.startswith(".") and name.endswith(".icloud") else name
                if (real.lower(), r["size"]) in local_index:
                    w.writerow([r["surface"], r["size"], r["path"]])

    surfaces = sorted({r["surface"] for r in rows})
    lines = ["# Dedup plan (dry run: nothing has moved)", "",
             f"{len(rows)} files scanned across {len(surfaces)} surfaces · {len(to_hash)} local files hashed (size collisions) · "
             f"{sum(bool(r['hashes']) and not r['local'] for r in rows)} cloud files matched by provider checksum · "
             f"{len(groups)} exact-duplicate groups", "", "| Surface | Files | Cloud-only | Legal-flagged | Reclaimable (archive) |", "|---|---|---|---|---|"]
    for s in surfaces:
        sr = [r for r in rows if r["surface"] == s]
        lines.append(f"| {s} | {len(sr)} | {sum(not r['local'] for r in sr)} | {sum(r['legal'] for r in sr)} | {human(reclaim[s])} |")
    lines += ["", f"**Total reclaimable:** {human(sum(reclaim.values()))}", "",
              "Review `duplicates.csv` (action=archive rows), `near-duplicates.csv` (manual review), `cloud-probable.csv` (verify).",
              "Legal-flagged groups are marked `flag-legal` and will not be moved.", "",
              "Apply (after approval): `python3 ops/dedup/dedup_apply.py --plan <dir>/duplicates.csv --archive-root /Volumes/<SSD>/Dedup-Archive --apply`",
              "Duplicates inside one cloud account (Google Drive, pCloud): `python3 ops/dedup/cloud_apply.py --plan <dir>/duplicates.csv` "
              "(moves them into that account's own `_Dedup-Archive` folder; nothing is downloaded or deleted)"]
    (a.indir / "PLAN.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines[:3] + [f"  reclaimable: {human(sum(reclaim.values()))} → {a.indir / 'PLAN.md'}"]))


if __name__ == "__main__":
    main()
