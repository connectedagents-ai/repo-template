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


def fake_rclone(tmp, files):
    fake = tmp / "fake"
    (tmp / "bin").mkdir(exist_ok=True)
    fake.mkdir(exist_ok=True)
    rc = tmp / "bin/rclone"
    rc.write_text(FAKE_RCLONE)
    rc.chmod(rc.stat().st_mode | stat.S_IEXEC)
    for path, items in files.items():
        (fake / (path.replace("/", "_").replace(":", "_") + ".json")).write_text(json.dumps(items))
    return {"PATH": f"{tmp / 'bin'}:{os.environ['PATH']}", "FAKE": str(fake)}


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
        return fake_rclone(self.tmp, files)

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
                                "gdrive-work:Reports/report.pdf": [{"Path": "report.pdf", "Hashes": {"md5": MD5}}],
                                "gdrive-work:B/x.pdf": [{"Path": "x.pdf", "Hashes": {"md5": "different"}}],
                                "gdrive-work:A/x.pdf": [{"Path": "x.pdf", "Hashes": {"md5": "y"}}]})
        r = self.run_py(CLOUD_APPLY, "--plan", plan, "--out", self.tmp, "--apply", env=env)
        moves = (self.tmp / "fake/moves").read_text().splitlines()
        self.assertEqual(len(moves), 1)
        self.assertTrue(moves[0].startswith("gdrive-work:Old/report (1).pdf -> gdrive-work:_Dedup-Archive/"))
        self.assertIn("changed since scan", r.stdout)
        (restore,) = self.tmp.glob("cloud-dedup-*/restore.sh")
        self.assertIn("rclone moveto", restore.read_text())
        subprocess.run(["bash", "-n", str(restore)], check=True)


class CloudApplyKeeperTest(TempDirTest):
    def test_duplicate_is_not_archived_when_the_keeper_changed(self):
        plan = self.tmp / "plan.csv"
        with open(plan, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["group", "sha256", "size", "action", "surface", "path", "hashes"])
            w.writerow([1, "md5:m", 10, "keep", "gdrive-work", "gdrive-work:K/a.pdf", "md5:m"])
            w.writerow([1, "md5:m", 10, "archive", "gdrive-work", "gdrive-work:D/a.pdf", "md5:m"])
        env = fake_rclone(self.tmp, {"gdrive-work:D/a.pdf": [{"Path": "a.pdf", "Hashes": {"md5": "m"}}],
                                "gdrive-work:K/a.pdf": [{"Path": "a.pdf", "Hashes": {"md5": "edited"}}]})
        r = self.run_py(CLOUD_APPLY, "--plan", plan, "--out", self.tmp, "--apply", env=env)
        self.assertIn("keeper missing or changed since scan", r.stdout)
        self.assertFalse((self.tmp / "fake/moves").exists())


    def test_duplicate_is_not_archived_when_the_local_keeper_was_edited(self):
        keeper = self.tmp / "keep.pdf"
        keeper.write_bytes(BODY)
        plan = self.tmp / "plan.csv"
        with open(plan, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["group", "sha256", "size", "action", "surface", "path", "hashes"])
            w.writerow([1, "x", len(BODY), "keep", "mac-local", str(keeper), f"md5:{MD5}"])
            w.writerow([1, "x", len(BODY), "archive", "gdrive-work", "gdrive-work:D/a.pdf", f"md5:{MD5}"])
        env = fake_rclone(self.tmp, {"gdrive-work:D/a.pdf": [{"Path": "a.pdf", "Hashes": {"md5": MD5}}]})
        keeper.write_bytes(BODY + b"edited")
        r = self.run_py(CLOUD_APPLY, "--plan", plan, "--out", self.tmp, "--apply", "--allow-cross-surface", env=env)
        self.assertIn("keeper missing or changed since scan", r.stdout)
        self.assertFalse((self.tmp / "fake/moves").exists())
        keeper.write_bytes(BODY)
        self.run_py(CLOUD_APPLY, "--plan", plan, "--out", self.tmp, "--apply", "--allow-cross-surface", env=env)
        self.assertEqual(len((self.tmp / "fake/moves").read_text().splitlines()), 1)


class InventoryFilesTest(TempDirTest):
    def test_folder_scans_of_one_account_keep_separate_files_and_overlaps_count_once(self):
        run = self.tmp / "run"
        docs = self.tmp / "docs.json"
        docs.write_text(lsjson([{"Path": "a.pdf", "Size": 9, "ModTime": "2025-01-01T00:00:00Z", "Hashes": {"md5": "q"}}]))
        arch = self.tmp / "arch.json"
        arch.write_text(lsjson([{"Path": "old/a.pdf", "Size": 9, "ModTime": "2025-01-01T00:00:00Z", "Hashes": {"md5": "q"}}]))
        whole = self.tmp / "whole.json"
        whole.write_text(lsjson([{"Path": "Shared Documents/a.pdf", "Size": 9, "ModTime": "2025-01-01T00:00:00Z", "Hashes": {"md5": "q"}}]))
        self.run_py(CLOUD_INV, "--remote", "sp-legal:Shared Documents", "--from-json", docs, "--out", run)
        self.run_py(CLOUD_INV, "--remote", "sp-legal:Archive", "--from-json", arch, "--out", run)
        self.run_py(CLOUD_INV, "--remote", "sp-legal:", "--from-json", whole, "--out", run)
        self.assertEqual(len(list(run.glob("inventory-sp-legal*.csv"))), 3)
        self.run_py(MERGE, "--in", run)
        with open(run / "duplicates.csv", newline="") as f:
            paths = sorted(r["path"] for r in csv.DictReader(f))
        self.assertEqual(paths, ["sp-legal:Archive/old/a.pdf", "sp-legal:Shared Documents/a.pdf"])


    def test_folders_that_clean_up_to_the_same_name_keep_separate_files(self):
        run = self.tmp / "run"
        for folder, name in (("Client A", "a.pdf"), ("Client_A", "b.pdf")):
            listing = self.tmp / f"{name}.json"
            listing.write_text(lsjson([{"Path": name, "Size": 9, "ModTime": "2025-01-01T00:00:00Z", "Hashes": {"md5": name}}]))
            self.run_py(CLOUD_INV, "--remote", f"sp-legal:{folder}", "--from-json", listing, "--out", run)
        self.assertEqual(len(list(run.glob("inventory-sp-legal_Client_A-*.csv"))), 2)

    def test_the_newest_scan_wins_when_scans_overlap(self):
        run = self.tmp / "run"
        old = self.tmp / "old.json"
        old.write_text(lsjson([{"Path": "Docs/a.pdf", "Size": 9, "ModTime": "2025-01-01T00:00:00Z", "Hashes": {"md5": "stale"}}]))
        new = self.tmp / "new.json"
        new.write_text(lsjson([{"Path": "a.pdf", "Size": 9, "ModTime": "2025-01-01T00:00:00Z", "Hashes": {"md5": "fresh"}},
                               {"Path": "b.pdf", "Size": 9, "ModTime": "2025-01-01T00:00:00Z", "Hashes": {"md5": "fresh"}}]))
        self.run_py(CLOUD_INV, "--remote", "sp-legal:", "--from-json", old, "--out", run)
        self.run_py(CLOUD_INV, "--remote", "sp-legal:Docs", "--from-json", new, "--out", run)
        (whole,) = run.glob("inventory-sp-legal.csv")
        os.utime(whole, (1, 1))  # the whole-account scan is older, though its name sorts first
        self.run_py(MERGE, "--in", run)
        with open(run / "duplicates.csv", newline="") as f:
            paths = sorted(r["path"] for r in csv.DictReader(f))
        self.assertEqual(paths, ["sp-legal:Docs/a.pdf", "sp-legal:Docs/b.pdf"])


class QuickXorHashTest(TempDirTest):
    """Reference values produced by `rclone hashsum quickxor` (rclone v1.71.1)."""

    def setUp(self):
        super().setUp()
        import sys
        sys.path.insert(0, str(OPS / "dedup"))
        from quickxorhash import QuickXorHash
        self.Q = QuickXorHash

    def test_matches_rclone_reference_values_in_one_pass_and_in_pieces(self):
        import random
        rnd = random.Random(7)
        big = bytes(rnd.getrandbits(8) for _ in range(100000))
        cases = {b"hello world": "6828031bd8f00610dce10d726b03190000000000", b"": "0" * 40,
                 big: "76874c5778b6fda87f1464ce09f578b6017be7ff"}
        for data, want in cases.items():
            self.assertEqual(self.Q().update(data).hexdigest(), want)
            h = self.Q()
            for k in range(0, len(data), 977):
                h.update(data[k:k + 977])
            self.assertEqual(h.hexdigest(), want)

    def test_onedrive_copy_matches_local_file_by_quickxor(self):
        home, run = self.tmp / "home", self.tmp / "run"
        home.mkdir()
        (home / "deck.pdf").write_bytes(b"hello world")
        listing = self.tmp / "od.json"
        listing.write_text(lsjson([{"Path": "Docs/deck.pdf", "Size": 11, "ModTime": "2025-01-01T00:00:00Z",
                                    "Hashes": {"quickxor": "6828031bd8f00610dce10d726b03190000000000"}}]))
        self.run_py(SCAN, "--surface", "mac-local", "--root", home, "--out", run)
        self.run_py(CLOUD_INV, "--remote", "onedrive-work:", "--from-json", listing, "--out", run)
        self.run_py(MERGE, "--in", run, "--prefer", "mac-local")
        with open(run / "duplicates.csv", newline="") as f:
            actions = {r["path"]: r["action"] for r in csv.DictReader(f)}
        self.assertEqual(actions, {str(home / "deck.pdf"): "keep", "onedrive-work:Docs/deck.pdf": "archive"})


class CloudReviewFixesTest(TempDirTest):
    def test_archive_folder_is_not_listed_again_and_nanosecond_times_parse(self):
        listing = self.tmp / "l.json"
        listing.write_text(lsjson([
            {"Path": "Docs/a.pdf", "Size": 5, "ModTime": "2025-03-04T05:06:07.123456789Z", "Hashes": {"md5": "m"}},
            {"Path": "_Dedup-Archive/20260101-000000/Docs/a.pdf", "Size": 5, "ModTime": "2025-03-04T05:06:07Z", "Hashes": {"md5": "m"}},
        ]))
        self.run_py(CLOUD_INV, "--remote", "gdrive-x:", "--from-json", listing, "--out", self.tmp)
        with open(self.tmp / "inventory-gdrive-x.csv", newline="") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual([r["path"] for r in rows], ["gdrive-x:Docs/a.pdf"])
        self.assertEqual(rows[0]["mtime"], "1741064767")

    def test_only_the_named_cloudstorage_folders_are_skipped(self):
        home, out = self.tmp / "home", self.tmp / "out"
        for acct in ("GoogleDrive-a@x.com", "GoogleDrive-b@x.com", "OneDrive-Personal"):
            (home / "Library/CloudStorage" / acct).mkdir(parents=True)
            (home / "Library/CloudStorage" / acct / "f.txt").write_text(acct)
        env = {**os.environ, "HOME": str(home), "OUT": str(out), "SKIP_CLOUDSTORAGE": "GoogleDrive-a@x.com"}
        subprocess.run(["bash", str(OPS / "dedup/run_dedup.sh")], env=env, capture_output=True, text=True, check=True)
        (run,) = out.iterdir()
        names = sorted(p.name for p in run.glob("inventory-*.csv"))
        self.assertIn("inventory-googledrive-b-x.com.csv", names)
        self.assertIn("inventory-onedrive-personal.csv", names)
        self.assertNotIn("inventory-googledrive-a-x.com.csv", names)

    def test_icloud_drive_can_be_left_out(self):
        home, out = self.tmp / "home", self.tmp / "out"
        icloud = home / "Library/Mobile Documents/com~apple~CloudDocs"
        icloud.mkdir(parents=True)
        (icloud / "f.txt").write_text("x")
        for skip, expected in (("0", True), ("1", False)):
            env = {**os.environ, "HOME": str(home), "OUT": str(out / skip), "SKIP_ICLOUD": skip}
            subprocess.run(["bash", str(OPS / "dedup/run_dedup.sh")], env=env, capture_output=True, text=True, check=True)
            (run,) = (out / skip).iterdir()
            self.assertEqual((run / "inventory-icloud-drive.csv").exists(), expected)
