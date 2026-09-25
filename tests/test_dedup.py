import csv, importlib.util, io, subprocess
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock
from tests.helpers import OPS, TempDirTest

SCAN, MERGE, APPLY = (OPS / "dedup" / n for n in ("dedup_scan.py", "dedup_merge.py", "dedup_apply.py"))


class DedupPipelineTest(TempDirTest):
    def plan(self, files):
        """Write files under tmp/home, run scan + merge, return the run dir."""
        home, run = self.tmp / "home", self.tmp / "run"
        for rel, body in files.items():
            (home / rel).parent.mkdir(parents=True, exist_ok=True)
            (home / rel).write_text(body)
        self.run_py(SCAN, "--surface", "mac-local", "--root", home, "--out", run)
        self.run_py(MERGE, "--in", run, "--prefer", "mac-local")
        return home, run

    def rows(self, run):
        with open(run / "duplicates.csv", newline="") as f:
            return list(csv.DictReader(f))

    def test_legal_paths_are_never_planned_for_archive(self):
        _, run = self.plan({"a/court-filing.pdf": "x" * 50, "b/court-filing copy.pdf": "x" * 50})
        self.assertNotIn("archive", {r["action"] for r in self.rows(run)})

    def test_apply_moves_duplicate_and_restore_script_puts_it_back(self):
        weird = "b/it's $(touch pwned) \"q\".txt"
        home, run = self.plan({"a/report.txt": "same" * 20, weird: "same" * 20})
        archive = self.tmp / "archive"
        self.run_py(APPLY, "--plan", run / "duplicates.csv", "--archive-root", archive, "--allow-internal", "--apply")
        self.assertEqual(sum(1 for p in [home / "a/report.txt", home / weird] if p.exists()), 1)
        (restore,) = archive.glob("*/restore.sh")
        subprocess.run(["bash", str(restore)], check=True, cwd=self.tmp)
        self.assertTrue((home / weird).exists() and (home / "a/report.txt").exists())
        self.assertFalse((self.tmp / "pwned").exists())

    def test_cloud_sync_and_icloud_files_are_skipped_without_opt_in(self):
        _, run = self.plan({"Library/CloudStorage/GoogleDrive-x/f.txt": "d" * 30,
                            "Library/Mobile Documents/com~apple~CloudDocs/f.txt": "d" * 30,
                            "Library/CloudStorage/GoogleDrive-x/g.txt": "d" * 30})
        r = self.run_py(APPLY, "--plan", run / "duplicates.csv", "--archive-root", self.tmp / "ar", "--allow-internal", "--apply")
        self.assertIn("moved: 0", r.stdout)
        self.assertIn("cloud-sync folder", r.stdout)

    def test_archive_root_must_be_external_by_default(self):
        _, run = self.plan({"a.txt": "z" * 10, "b.txt": "z" * 10})
        r = self.run_py(APPLY, "--plan", run / "duplicates.csv", "--archive-root", self.tmp / "ar", check=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("refusing", r.stderr)

    def test_a_failing_move_does_not_stop_the_run(self):
        home, run = self.plan({"k/x.txt": "m" * 40, "d1/x.txt": "m" * 40, "d2/x.txt": "m" * 40})
        spec = importlib.util.spec_from_file_location("dedup_apply", APPLY)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        real_move = mod.shutil.move
        calls = []

        def flaky_move(src, dst):
            calls.append(src)
            if len(calls) == 1:
                raise OSError("disk went away")
            return real_move(src, dst)

        args = ["dedup_apply.py", "--plan", str(run / "duplicates.csv"), "--archive-root", str(self.tmp / "ar"),
                "--allow-internal", "--apply"]
        out = io.StringIO()
        with mock.patch.object(mod.shutil, "move", flaky_move), mock.patch("sys.argv", args), \
                redirect_stdout(out), redirect_stderr(io.StringIO()):
            mod.main()
        self.assertEqual(len(calls), 2)
        self.assertIn("moved: 1", out.getvalue())
        (manifest,) = (self.tmp / "ar").glob("*/MANIFEST.tsv")
        self.assertEqual(len(manifest.read_text().splitlines()), 2)
        self.assertTrue((manifest.parent / "restore.sh").stat().st_mode & 0o100)
