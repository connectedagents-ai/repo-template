import csv, json, os, stat, subprocess
from tests.helpers import OPS, TempDirTest

CONSOLIDATE = OPS / "dedup/consolidate_to_drive.py"

# Fake rclone backed by a folder: copyto stores the file's md5 as an lsjson answer; lsjson reads it back.
# $BAD_HASH makes uploads land with a wrong checksum; $READONLY makes the remote read-only.
FAKE_RCLONE = r'''#!/bin/bash
key() { printf '%s' "$1" | tr '/: ' '___'; }
case "$1" in
  config) [ -n "$READONLY" ] && echo "scope = drive.readonly" || echo "scope = drive" ;;
  lsjson) f="$FAKE/$(key "${@: -1}").json"; [ -f "$f" ] && cat "$f" || echo "[]" ;;
  copyto) src="$3"; dst="$4"; sum=$(python3 -c 'import hashlib,sys; print(hashlib.md5(open(sys.argv[1],"rb").read()).hexdigest())' "$src"); [ -n "$BAD_HASH" ] && sum=bad
          printf '[{"Path":"x","Hashes":{"md5":"%s"}}]' "$sum" > "$FAKE/$(key "$dst").json"; echo "$dst" >> "$FAKE/copies" ;;
esac
'''


class ConsolidateTest(TempDirTest):
    def setUp(self):
        super().setUp()
        self.src, self.archive, fake = self.tmp / "sort", self.tmp / "archive", self.tmp / "fake"
        (self.tmp / "bin").mkdir()
        fake.mkdir()
        rc = self.tmp / "bin/rclone"
        rc.write_text(FAKE_RCLONE)
        rc.chmod(rc.stat().st_mode | stat.S_IEXEC)
        self.env = {"PATH": f"{self.tmp / 'bin'}:{os.environ['PATH']}", "FAKE": str(fake)}
        for rel, body in {"stmts/jan.pdf": "jan", "stmts/feb.pdf": "feb", "notes/app.js": "js",
                          "repo/.git/HEAD": "ref", "repo/doc.pdf": "in a repo"}.items():
            (self.src / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.src / rel).write_text(body)

    def consolidate(self, *extra, env=None, check=True):
        return self.run_py(CONSOLIDATE, "--root", self.src, "--dest", "gdrive-me:Master", "--archive-root", self.archive,
                           "--ext", "pdf", *extra, env={**self.env, **(env or {})}, check=check)

    def copies(self):
        f = self.tmp / "fake/copies"
        return f.read_text().split() if f.exists() else []

    def test_dry_run_lists_documents_only_and_changes_nothing(self):
        r = self.consolidate()
        self.assertIn("2 files", r.stdout)
        self.assertNotIn("app.js", r.stdout)
        self.assertNotIn("repo/doc.pdf", r.stdout)
        self.assertEqual(self.copies(), [])
        self.assertTrue((self.src / "stmts/jan.pdf").exists())

    def test_apply_copies_verifies_then_archives_and_restore_puts_files_back(self):
        self.consolidate("--apply")
        self.assertEqual(sorted(self.copies()), ["gdrive-me:Master/stmts/feb.pdf", "gdrive-me:Master/stmts/jan.pdf"])
        self.assertFalse((self.src / "stmts/jan.pdf").exists())
        (run,) = self.archive.glob("consolidate-*")
        with open(run / "MANIFEST.tsv", newline="") as f:
            self.assertEqual({r["status"] for r in csv.DictReader(f, delimiter="\t")}, {"verified"})
        subprocess.run(["bash", str(run / "restore.sh")], check=True)
        self.assertEqual((self.src / "stmts/jan.pdf").read_text(), "jan")

    def test_unverified_upload_leaves_local_file_in_place(self):
        r = self.consolidate("--apply", env={"BAD_HASH": "1"})
        self.assertIn("not verified (left in place): 2", r.stdout)
        self.assertTrue((self.src / "stmts/jan.pdf").exists())

    def test_existing_different_file_is_a_conflict_not_overwritten(self):
        key = "gdrive-me_Master_stmts_jan.pdf"
        (self.tmp / f"fake/{key}.json").write_text(json.dumps([{"Path": "jan.pdf", "Hashes": {"md5": "other"}}]))
        r = self.consolidate("--apply")
        self.assertIn("conflicts (left in place): 1", r.stdout)
        self.assertNotIn("gdrive-me:Master/stmts/jan.pdf", self.copies())
        self.assertTrue((self.src / "stmts/jan.pdf").exists())

    def test_plan_leaves_out_planned_duplicates(self):
        plan = self.tmp / "duplicates.csv"
        plan.write_text("group,sha256,size,action,surface,path,hashes\n"
                        f"1,x,3,archive,mac-local,{self.src / 'stmts/feb.pdf'},\n")
        r = self.consolidate("--plan", plan)
        self.assertIn("1 files", r.stdout)
        self.assertNotIn("feb.pdf", r.stdout.split("planned duplicates")[1])

    def test_refuses_read_only_remote_and_git_work_tree(self):
        r = self.consolidate("--apply", env={"READONLY": "1"}, check=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("scope=drive", r.stderr)
        r = self.run_py(CONSOLIDATE, "--root", self.src / "repo", "--dest", "gdrive-me:M", "--archive-root", self.archive,
                        env=self.env, check=False)
        self.assertIn("git work tree", r.stderr)
