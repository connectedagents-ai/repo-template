#!/usr/bin/env python3
"""consolidate_to_drive.py — move a local document set into ONE master folder in a cloud account (Google Drive, OneDrive, …).

    python3 consolidate_to_drive.py --root ~/Desktop/"DESKTOP SORT" --ext pdf --ext xlsx \
        --dest "gdrive-personal:Master Folder/Incoming" --archive-root /Volumes/SSD/Consolidated     # DRY RUN
    python3 consolidate_to_drive.py ... --plan <run>/duplicates.csv --apply                         # after approval

Each file goes to <dest>/<path relative to --root>. Safety:
- DRY RUN by default. Never deletes and never overwrites: a destination file with different content, or one
  whose checksum can't be read, is reported as a conflict. A destination that doesn't exist yet (new folder) is created.
- Per file: `rclone copyto --checksum`, then the destination is re-listed and its checksum must equal the local file's.
  Only then is the local original moved (not deleted) into <archive-root>/<stamp>/<rel>. Unverified files stay where they are.
- --plan <duplicates.csv> (from dedup_merge.py) leaves out every row planned as `archive`, so only one copy of each duplicate goes up.
- Skips build/dependency folders and every git repo under --root; refuses a --root inside a git work tree.
- Refuses a read-only Google Drive remote (connect_cloud.sh default) and says how to allow writes.
- MANIFEST.tsv and restore.sh (puts local files back; the cloud copy stays) are written and flushed after every file.
"""
import argparse, base64, csv, datetime, json, os, re, shlex, shutil, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dedup_merge import file_hashes  # noqa: E402
from dedup_scan import SKIP_DIRS, extension, inside_git_tree  # noqa: E402

COMPARABLE = ("md5", "sha1", "sha256", "quickxor")


def hex_value(v):
    """Checksums as lowercase hex; a base64 QuickXor (28 chars) is decoded."""
    return base64.b64decode(v).hex() if re.fullmatch(r"[A-Za-z0-9+/]{27}=", v) else v.lower()


def hash_name(name):
    """rclone versions spell hash types differently (MD5 / md5, SHA-1 / sha1, QuickXorHash / quickxor)."""
    n = name.lower().replace("-", "")
    return "quickxor" if n.startswith("quickxor") else n


def rclone(*args):
    return subprocess.run(["rclone", *args], capture_output=True, text=True)


NOT_FOUND = (3, 4)  # rclone exit codes: 3 directory not found, 4 file not found


def remote_state(path):
    """("missing", None) if no file is there yet (new folders included), ("exists", {checksums, maybe empty}) if one is,
    ("error", None) for any other listing failure (auth, network, quota)."""
    r = rclone("lsjson", "--hash", "--files-only", path)
    if r.returncode in NOT_FOUND or (r.returncode != 0 and "not found" in r.stderr.lower()):
        return "missing", None
    if r.returncode != 0:
        return "error", None
    items = json.loads(r.stdout or "[]")
    if not items:
        return "missing", None
    return "exists", {hash_name(t): hex_value(v) for t, v in (items[0].get("Hashes") or {}).items() if v}


def same_content(local, remote):
    types = [t for t in COMPARABLE if t in (remote or {})]
    if not types:
        return False
    mine = file_hashes(local, types)
    return any(mine.get(t) == remote[t] for t in types)


def sources(root, exts, skip):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not os.path.lexists(os.path.join(dirpath, d, ".git"))]
        for name in sorted(filenames):
            p = Path(dirpath) / name
            if name == ".DS_Store" or (exts and extension(name) not in exts) or os.path.realpath(p) in skip or not p.is_file():
                continue
            yield p


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", required=True, type=Path, help="local folder to consolidate")
    ap.add_argument("--dest", required=True, help="rclone remote and master folder, e.g. 'gdrive-personal:Master/Incoming'")
    ap.add_argument("--archive-root", required=True, type=Path, help="where verified local originals are moved")
    ap.add_argument("--ext", action="append", default=[], help="only these file types (repeatable)")
    ap.add_argument("--plan", type=Path, help="duplicates.csv from dedup_merge.py: rows planned as archive are left out")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    root = a.root.expanduser().resolve()
    if not root.is_dir():
        sys.exit(f"no folder at {root}")
    if inside_git_tree(root):
        sys.exit(f"refusing: {root} is inside a git work tree (code is pushed with git, not copied to Drive)")
    if ":" not in a.dest:
        sys.exit("--dest must be an rclone remote, e.g. gdrive-personal:Master")
    remote = a.dest.split(":", 1)[0]
    dest = a.dest.rstrip("/")
    skip = set()
    if a.plan:
        with open(a.plan, newline="", encoding="utf-8") as f:
            skip = {os.path.realpath(os.path.expanduser(r["path"])) for r in csv.DictReader(f) if r["action"] == "archive"}
    exts = {e.lower().lstrip(".") for e in a.ext}
    files = list(sources(root, exts, skip))
    print(f"{len(files)} files under {root} -> {dest}" + (f" ({len(skip)} planned duplicates left out)" if skip else ""))
    if not a.apply:
        for p in files:
            print(f"  would copy {p} -> {dest}/{p.relative_to(root).as_posix()}")
        print("DRY RUN. Re-run with --apply after approval.")
        return
    cfg = rclone("config", "show", remote)
    if "drive.readonly" in cfg.stdout:
        sys.exit(f"refusing: remote {remote} is read-only. Allow writes with: rclone config update {remote} scope=drive")
    run = a.archive_root.expanduser() / f"consolidate-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
    run.mkdir(parents=True)
    moved = conflicts = failed = 0
    with open(run / "MANIFEST.tsv", "w") as man, open(run / "restore.sh", "w") as rs:
        man.write("status\tfrom\tto_remote\tarchived_to\n")
        rs.write("#!/bin/bash\n# Put consolidated files back in place (the cloud copies stay)\nset -e\n")
        for p in files:
            rel = p.relative_to(root).as_posix()
            target = f"{dest}/{rel}"
            state, before = remote_state(target)
            if state == "error":
                status = "list-failed"
            elif state == "exists" and not same_content(p, before):
                status = "conflict"  # different, or no checksum to prove it's the same: never overwrite
            elif state == "missing" and rclone("copyto", "--checksum", "--ignore-existing", str(p), target).returncode != 0:
                status = "copy-failed"
            else:
                after_state, after = remote_state(target)
                status = "verified" if after_state == "exists" and same_content(p, after) else "unverified"
            archived = ""
            if status == "verified":
                archived = run / "files" / rel
                archived.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(p), str(archived))
                rs.write(f"mkdir -p {shlex.quote(str(p.parent))} && mv {shlex.quote(str(archived))} {shlex.quote(str(p))}\n")
                moved += 1
            elif status == "conflict":
                conflicts += 1
            else:
                failed += 1
            man.write(f"{status}\t{p}\t{target}\t{archived}\n")
            man.flush()
            rs.flush()
            print(f"  {status:<12} {rel}")
    os.chmod(run / "restore.sh", 0o755)
    print(f"verified + archived locally: {moved}; conflicts or unverifiable existing files (left in place): {conflicts}; not verified (left in place): {failed}")
    print(f"Manifest: {run / 'MANIFEST.tsv'}   Undo: bash {shlex.quote(str(run / 'restore.sh'))}")


if __name__ == "__main__":
    main()
