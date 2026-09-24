import csv, hashlib, json, os, stat, subprocess
from tests.helpers import OPS, TempDirTest

SCAN, MERGE, APPLY = (OPS / "dedup" / n for n in ("dedup_scan.py", "dedup_merge.py", "dedup_apply.py"))
CLOUD_INV, CLOUD_APPLY = OPS / "dedup/cloud_inventory.py", OPS / "dedup/cloud_apply.py"
BODY = b"quarterly report contents" * 10
MD5 = hashlib.md5(BODY).hexdigest()

# Fake rclone: lsjson answers from $FAKE/<path-with-slashes-as-_>.json, moveto records the move.
FAKE_RCLONE = r'''#!/bin/bash
case "$1" in
  lsjson) f="$FAKE/$(printf '%s' "${@: -1}" | tr '/:' '__').json"; [ -f "$f" ] && cat "$f" || echo "[]" ;;
  moveto) echo "$2 -> $3" >> "$FAKE/moves" ;;
  listremotes) printf 'gdrive-work: drive\n' ;;
esac
'''


def lsjson(items):
    return "[\n" + ",\n".join(json.dumps(i) for i in items) + "\n]\n"


class CloudDedupTest(TempDirTest):
    def setUp(self):
        super().setUp()
        self.run_dir = self.tmp / "run"
        self.home = self.tmp / "home"
        (self.home / "Docs").mkdir(parents=True)
        (self.home / "Docs/report.pdf").write_bytes(BODY)
        listing = self.tmp / "drive.json"
        listing.write_text(lsjson([
            {"Path": "Reports/report.pdf", "Size": len(BODY), "ModTime": "2025-01-02T03:04:05Z", "Hashes": {"md5": MD5}},
            {"Path": "Old/report (1).pdf", "Size": len(BODY), "ModTime": "2025-02-02T03:04:05Z", "Hashes": {"md5": MD5}},
            {"Path": "Notes", "Size": -1, "IsDir": True},
            {"Path": "Budget.gsheet", "Size": -1, "ModTime": "2025-01-01T00:00:00Z"},
            {"Path": "Legal/court filing.pdf", "Size": 99, "ModTime": "2025-01-01T00:00:00Z", "Hashes": {"md5": "x"}},
        ]))
        self.run_py(SCAN, "--surface", "mac-local", "--root", self.home, "--out", self.run_dir)
        self.run_py(CLOUD_INV, "--remote", "gdrive-work:", "--from-json", listing, "--out", self.run_dir)
        self.run_py(MERGE, "--in", self.run_dir, "--prefer", "mac-local")

    def plan(self):
        with open(self.run_dir / "duplicates.csv", newline="") as f:
            return list(csv.DictReader(f))

    def test_inventory_skips_folders_and_google_docs_and_flags_legal(self):
        with open(self.run_dir / "inventory-gdrive-work.csv", newline="") as f:
            rows = {r["path"]: r for r in csv.DictReader(f)}
        self.assertEqual(set(rows), {"gdrive-work:Reports/report.pdf", "gdrive-work:Old/report (1).pdf",
                                     "gdrive-work:Legal/court filing.pdf"})
        self.assertEqual(rows["gdrive-work:Legal/court filing.pdf"]["legal"], "1")

    def test_local_file_matches_cloud_copies_by_provider_checksum_without_download(self):
        rows = self.plan()
        self.assertEqual(len({r["group"] for r in rows}), 1)
        by_path = {r["path"]: r["action"] for r in rows}
        self.assertEqual(by_path[str(self.home / "Docs/report.pdf")], "keep")
        self.assertEqual(by_path["gdrive-work:Reports/report.pdf"], "archive")

    def test_local_apply_leaves_cloud_rows_alone(self):
        r = self.run_py(APPLY, "--plan", self.run_dir / "duplicates.csv", "--archive-root", self.tmp / "ar", "--allow-internal")
        self.assertIn("cloud-account file", r.stdout)
        self.assertIn("would move: 0", r.stdout)

    def fake_rclone(self, files):
        fake = self.tmp / "fake"
        (self.tmp / "bin").mkdir(exist_ok=True)
        fake.mkdir(exist_ok=True)
        rc = self.tmp / "bin/rclone"
        rc.write_text(FAKE_RCLONE)
        rc.chmod(rc.stat().st_mode | stat.S_IEXEC)
        for path, items in files.items():
            (fake / (path.replace("/", "_").replace(":", "_") + ".json")).write_text(json.dumps(items))
        return {"PATH": f"{self.tmp / 'bin'}:{os.environ['PATH']}", "FAKE": str(fake)}

    def test_cloud_apply_only_archives_when_keeper_is_in_the_same_account(self):
        env = self.fake_rclone({})
        r = self.run_py(CLOUD_APPLY, "--plan", self.run_dir / "duplicates.csv", "--out", self.tmp, "--apply", env=env)
        self.assertIn("keeper not in the same account", r.stdout)
        self.assertFalse((self.tmp / "fake/moves").exists())

    def test_cloud_apply_moves_server_side_after_recheck_and_writes_undo(self):
        plan = self.tmp / "plan.csv"
        with open(plan, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["group", "sha256", "size", "action", "surface", "path", "hashes"])
            w.writerow([1, f"md5:{MD5}", 10, "keep", "gdrive-work", "gdrive-work:Reports/report.pdf", f"md5:{MD5}"])
            w.writerow([1, f"md5:{MD5}", 10, "archive", "gdrive-work", "gdrive-work:Old/report (1).pdf", f"md5:{MD5}"])
            w.writerow([2, "md5:y", 10, "keep", "gdrive-work", "gdrive-work:A/x.pdf", "md5:y"])
            w.writerow([2, "md5:y", 10, "archive", "gdrive-work", "gdrive-work:B/x.pdf", "md5:y"])  # changed since scan
        env = self.fake_rclone({"gdrive-work:Old/report (1).pdf": [{"Path": "report (1).pdf", "Hashes": {"md5": MD5}}],
                                "gdrive-work:B/x.pdf": [{"Path": "x.pdf", "Hashes": {"md5": "different"}}]})
        r = self.run_py(CLOUD_APPLY, "--plan", plan, "--out", self.tmp, "--apply", env=env)
        moves = (self.tmp / "fake/moves").read_text().splitlines()
        self.assertEqual(len(moves), 1)
        self.assertTrue(moves[0].startswith("gdrive-work:Old/report (1).pdf -> gdrive-work:_Dedup-Archive/"))
        self.assertIn("changed since scan", r.stdout)
        (restore,) = self.tmp.glob("cloud-dedup-*/restore.sh")
        self.assertIn("rclone moveto", restore.read_text())
        subprocess.run(["bash", "-n", str(restore)], check=True)
