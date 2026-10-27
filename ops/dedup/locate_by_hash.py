#!/usr/bin/env python3
"""locate_by_hash.py — READ-ONLY: find where files live NOW, by fingerprint, after folders were moved or collapsed.

    python3 locate_by_hash.py --hashes release-725.csv --root ~ --root "/Volumes/SSD/Collapse-Archive" --out ~/ops-reports/locate
    python3 locate_by_hash.py --hashes hashes.txt --root ~/Desktop --algo md5 --out <dir>

--hashes: a CSV with a hash column (named hash, sha256, sha1, md5 or quickxor) and optional size, name and old_path columns,
or a plain text file with one hash per line. The hash type is detected from its form (64 hex = sha256, 40 = sha1, 32 = md5,
28-char base64 = quickxor) unless --algo is given.
Speed: when sizes are known, only files of a wanted size are hashed; files whose name matches a wanted name are hashed too.
Without sizes every file under the roots is hashed (slow on big trees: give sizes when you have them).
Writes <out>/located.csv (hash, old_path, current_path, copies, all_paths) and <out>/missing.csv, and prints the hit rate.
Never moves, renames or opens anything for writing. Skips build/dependency folders and iCloud placeholders (no downloads).
"""
import argparse, csv, os, re, stat, sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dedup_merge import file_hashes  # noqa: E402
from dedup_scan import SF_DATALESS, SKIP_DIRS, SKIP_SUFFIXES  # noqa: E402

HASH_COLS = ("hash", "sha256", "sha1", "md5", "quickxor", "fingerprint")


def detect(h):
    if re.fullmatch(r"[0-9a-f]{64}", h):
        return "sha256"
    if re.fullmatch(r"[0-9a-f]{40}", h):
        return "sha1"
    if re.fullmatch(r"[0-9a-f]{32}", h):
        return "md5"
    if re.fullmatch(r"[A-Za-z0-9+/]{27}=", h):
        return "quickxor"
    return None


def norm(h, algo):
    return h if algo == "quickxor" else h.lower()


def load(path, forced):
    """Return a list of wanted records: {hash, algo, size, name, old_path}."""
    text = Path(path).read_text(encoding="utf-8-sig")
    first = text.splitlines()[0] if text.strip() else ""
    rows = []
    if any(c in first.lower() for c in HASH_COLS) and ("," in first or "\t" in first):
        reader = csv.DictReader(text.splitlines(), dialect="excel-tab" if "\t" in first else "excel")
        col = next(c for c in reader.fieldnames if c.strip().lower() in HASH_COLS)
        for r in reader:
            low = {k.strip().lower(): (v or "").strip() for k, v in r.items() if k}
            rows.append({"hash": low.get(col.strip().lower(), ""), "size": low.get("size", ""),
                         "name": low.get("name", "") or os.path.basename(low.get("old_path", "") or low.get("path", "")),
                         "old_path": low.get("old_path", "") or low.get("path", "")})
    else:
        rows = [{"hash": ln.strip(), "size": "", "name": "", "old_path": ""} for ln in text.splitlines() if ln.strip()]
    out = []
    for r in rows:
        algo = forced or detect(r["hash"].lower()) or detect(r["hash"])
        if not r["hash"] or not algo:
            print(f"  skip unrecognized hash: {r['hash'][:20]!r}", file=sys.stderr)
            continue
        r["algo"], r["hash"] = algo, norm(r["hash"], algo)
        r["size"] = int(r["size"]) if str(r["size"]).isdigit() else None
        out.append(r)
    return out


def walk(roots):
    for root in roots:
        root = os.path.expanduser(root)
        if not os.path.isdir(root):
            print(f"  skip missing root {root}", file=sys.stderr)
            continue
        for dirpath, dirnames, filenames in os.walk(root, onerror=lambda e: None):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.endswith(SKIP_SUFFIXES)]
            for name in filenames:
                if name == ".DS_Store" or (name.startswith(".") and name.endswith(".icloud")):
                    continue
                p = os.path.join(dirpath, name)
                try:
                    st = os.lstat(p)
                except OSError:
                    continue
                if stat.S_ISREG(st.st_mode) and not (getattr(st, "st_flags", 0) & SF_DATALESS):
                    yield p, name, st.st_size


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--hashes", required=True, type=Path)
    ap.add_argument("--root", action="append", required=True)
    ap.add_argument("--algo", choices=["sha256", "sha1", "md5", "quickxor"], help="force the hash type instead of detecting it")
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    wanted = load(a.hashes, a.algo)
    if not wanted:
        sys.exit("no usable hashes in the list")
    algos = tuple(sorted({w["algo"] for w in wanted}))
    by_hash = {(w["algo"], w["hash"]): w for w in wanted}
    sizes = {w["size"] for w in wanted if w["size"] is not None}
    every_size_known = all(w["size"] is not None for w in wanted)
    names = {w["name"] for w in wanted if w["name"]}
    if not every_size_known:
        print("  note: some entries have no size, so every file under the roots is hashed (slower)", file=sys.stderr)
    found = defaultdict(list)
    hashed = 0
    for p, name, size in walk(a.root):
        if every_size_known and size not in sizes and name not in names:
            continue
        digests = file_hashes(p, algos)
        hashed += 1
        for algo, value in digests.items():
            key = (algo, norm(value, algo))
            if key in by_hash:
                found[key].append(p)
    a.out.mkdir(parents=True, exist_ok=True)
    hits = 0
    with open(a.out / "located.csv", "w", newline="") as f, open(a.out / "missing.csv", "w", newline="") as m:
        lw, mw = csv.writer(f), csv.writer(m)
        lw.writerow(["hash", "algo", "old_path", "current_path", "copies", "all_paths"])
        mw.writerow(["hash", "algo", "old_path", "name", "size"])
        for w in wanted:
            paths = sorted(found.get((w["algo"], w["hash"]), []))
            if paths:
                hits += 1
                same = [p for p in paths if w["old_path"] and os.path.abspath(os.path.expanduser(w["old_path"])) == p]
                lw.writerow([w["hash"], w["algo"], w["old_path"], (same or paths)[0], len(paths), "; ".join(paths)])
            else:
                mw.writerow([w["hash"], w["algo"], w["old_path"], w["name"], w["size"] if w["size"] is not None else ""])
    print(f"located {hits} of {len(wanted)} ({100 * hits // len(wanted)}%), hashed {hashed} candidate files → {a.out}/located.csv, missing.csv")


if __name__ == "__main__":
    main()
