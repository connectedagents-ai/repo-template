#!/usr/bin/env python3
"""cloud_inventory.py — phase 1 for cloud accounts (Google Drive, pCloud, and anything else rclone supports).

    python3 cloud_inventory.py --remote gdrive-powerconnection: --out <dir>
    python3 cloud_inventory.py --remote pcloud: --out <dir>

READ-ONLY and download-free: asks the provider for its file list and the checksums it already stores
(`rclone lsjson --hash`), so nothing is copied to this Mac. Writes <dir>/inventory-<remote>.csv in the same
format as dedup_scan.py plus a `hashes` column (e.g. "md5:…;sha1:…"), which dedup_merge.py uses to match cloud files
with each other and with local files. Google Docs/Sheets/Slides and Drive shortcuts are skipped (no stored checksum /
not real copies). Legal-looking paths are flagged like dedup_scan.py.
One-time setup: see connect_cloud.sh.
"""
import argparse, csv, datetime, json, re, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dedup_scan import DEFAULT_LEGAL  # noqa: E402

DRIVE_FLAGS = ["--drive-skip-gdocs", "--drive-skip-shortcuts"]


def remote_type(remote):
    out = subprocess.run(["rclone", "listremotes", "--long"], capture_output=True, text=True).stdout
    for line in out.splitlines():
        name, _, typ = line.partition(":")
        if f"{name}:" == remote:
            return typ.strip()
    return ""


def lsjson_lines(remote):
    """Stream `rclone lsjson` (one JSON object per line) without holding the whole listing in memory."""
    cmd = ["rclone", "lsjson", "-R", "--files-only", "--hash", "--fast-list", remote]
    if remote_type(remote) == "drive":
        cmd += DRIVE_FLAGS
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True)
    yield from p.stdout
    if p.wait() != 0:
        raise SystemExit(f"rclone could not list {remote} (exit {p.returncode}). Run: rclone lsd {remote}   to check the connection.")


def parse(lines):
    for line in lines:
        line = line.strip().rstrip(",")
        if line in ("", "[", "]"):
            continue
        yield json.loads(line)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--remote", required=True, help="rclone remote name with colon, e.g. gdrive-powerconnection:")
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--from-json", type=Path, help="read a saved `rclone lsjson -R --hash` output instead of calling rclone")
    ap.add_argument("--legal-pattern", default=DEFAULT_LEGAL)
    a = ap.parse_args()
    if not a.remote.endswith(":"):
        a.remote += ":"
    surface = re.sub(r"[^A-Za-z0-9._-]", "_", a.remote[:-1])
    legal = re.compile(a.legal_pattern, re.I)
    a.out.mkdir(parents=True, exist_ok=True)
    out = a.out / f"inventory-{surface}.csv"
    lines = open(a.from_json, encoding="utf-8") if a.from_json else lsjson_lines(a.remote)
    n = hashed = flagged = skipped = 0
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["surface", "path", "size", "mtime", "local", "legal", "hashes"])
        for item in parse(lines):
            size = int(item.get("Size", -1))
            if item.get("IsDir") or size <= 0:  # folders, Google-native docs (size -1) and empty files
                skipped += 1
                continue
            path = f"{a.remote}{item['Path']}"
            hashes = ";".join(f"{t}:{v}" for t, v in sorted((item.get("Hashes") or {}).items()) if v)
            try:
                mtime = int(datetime.datetime.fromisoformat(item.get("ModTime", "").replace("Z", "+00:00")).timestamp())
            except ValueError:
                mtime = 0
            is_legal = bool(legal.search(path))
            w.writerow([surface, path, size, mtime, 0, int(is_legal), hashes])
            n += 1
            hashed += bool(hashes)
            flagged += is_legal
    print(f"  {surface}: {n} files ({hashed} with provider checksums, {flagged} legal-flagged, {skipped} folders/Google docs/empty skipped) → {out}")


if __name__ == "__main__":
    main()
