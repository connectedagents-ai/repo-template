#!/usr/bin/env python3
"""jdupes_archive.py — turn a `jdupes -r -j` report into an archive plan. Dry run unless --apply. Never deletes.

    jdupes -r -j -q "$SSD" > "$RUN/jdupes.json"
    python3 jdupes_archive.py --json "$RUN/jdupes.json" --root "$SSD" --archive "$ARCH" --out "$RUN"          # plan only
    python3 jdupes_archive.py --json "$RUN/jdupes.json" --root "$SSD" --archive "$ARCH" --out "$RUN" --apply  # move

Per duplicate set: drops paths in skipped folders (archive, Trash, git repos, app bundles, Photos libraries, ._ files);
if any remaining path looks legal, the whole set is flagged `flag-legal` and nothing moves; otherwise the keeper is the
shortest path (then the oldest) and every other copy is planned `archive`.
--apply re-checks each copy byte-for-byte against its keeper, moves it to <archive>/<path relative to root>
(never overwriting), and appends to <archive>/MANIFEST.tsv and <archive>/restore.sh (run it to put everything back).
Writes <out>/plan.csv and prints the summary.
"""
import argparse, csv, filecmp, json, os, re, shlex, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dedup_scan import DEFAULT_LEGAL, SKIP_DIRS, SKIP_SUFFIXES  # noqa: E402


def skipped(path, root):
    parts = Path(os.path.relpath(path, root)).parts
    if Path(path).name.startswith("._") or Path(path).name == ".DS_Store":
        return True
    if any(p in SKIP_DIRS or p.endswith(SKIP_SUFFIXES) or p.startswith("_Dedup-Archive") for p in parts[:-1]):
        return True
    d = Path(path).parent
    while d != Path(root) and d != d.parent:  # inside a git work tree
        if (d / ".git").exists():
            return True
        d = d.parent
    return False


def plan(report, root, legal):
    rows = []
    for n, s in enumerate(report.get("matchSets", []), 1):
        paths = [os.path.abspath(f["filePath"]) for f in s["fileList"]]
        paths = [p for p in paths if not skipped(p, root)]
        if len(paths) < 2:
            continue
        if any(legal.search(p) for p in paths):
            rows += [(n, "flag-legal", s["fileSize"], p, "") for p in paths]
            continue
        keeper = min(paths, key=lambda p: (len(p), os.stat(p).st_mtime, p))
        rows.append((n, "keep", s["fileSize"], keeper, ""))
        rows += [(n, "archive", s["fileSize"], p, keeper) for p in sorted(paths) if p != keeper]
    return rows


def apply(rows, root, archive):
    archive.mkdir(parents=True, exist_ok=True)
    restore = archive / "restore.sh"
    new_restore = not restore.exists()
    moved = skipped_n = 0
    with open(archive / "MANIFEST.tsv", "a") as man, open(restore, "a") as rs:
        if new_restore:
            rs.write("#!/bin/bash\nset -u\n")
        for _, action, _, path, keeper in rows:
            if action != "archive":
                continue
            dest = archive / os.path.relpath(path, root)
            if not (os.path.isfile(path) and os.path.isfile(keeper)) or dest.exists() \
                    or not filecmp.cmp(path, keeper, shallow=False):
                print(f"  skip (changed, missing or already archived): {path}", file=sys.stderr)
                skipped_n += 1
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            os.rename(path, dest)
            man.write(f"{path}\t{dest}\t{keeper}\n")
            rs.write(f"mkdir -p {shlex.quote(os.path.dirname(path))} && mv -n {shlex.quote(str(dest))} {shlex.quote(path)}\n")
            moved += 1
    restore.chmod(0o755)
    return moved, skipped_n


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", required=True, type=Path, help="output of jdupes -r -j")
    ap.add_argument("--root", required=True, help="the folder jdupes scanned")
    ap.add_argument("--archive", required=True, type=Path, help="where archived copies go (same volume = instant moves)")
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--legal-pattern", default=DEFAULT_LEGAL)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    root = os.path.abspath(a.root)
    rows = plan(json.loads(a.json.read_text()), root, re.compile(a.legal_pattern, re.I))
    a.out.mkdir(parents=True, exist_ok=True)
    with open(a.out / "plan.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["set", "action", "size", "path", "keeper"])
        w.writerows(rows)
    arch = [r for r in rows if r[1] == "archive"]
    print(f"sets {len({r[0] for r in rows})} · archive {len(arch)} files, {sum(r[2] for r in arch) / 1e9:.2f} GB · "
          f"legal-hold {sum(r[1] == 'flag-legal' for r in rows)} files → {a.out}/plan.csv")
    if not a.apply:
        print("dry run: nothing moved. Review plan.csv, then re-run with --apply.")
        return
    moved, skipped_n = apply(rows, root, a.archive)
    print(f"moved {moved}, skipped {skipped_n} → {a.archive} (undo: bash {a.archive}/restore.sh)")


if __name__ == "__main__":
    main()
