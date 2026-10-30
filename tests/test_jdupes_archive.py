import csv, json, subprocess
from tests.helpers import OPS, TempDirTest

SCRIPT = OPS / "dedup/jdupes_archive.py"


class JdupesArchiveTest(TempDirTest):
    def setUp(self):
        super().setUp()
        self.ssd = self.tmp / "SSD"
        files = {"A/x.pdf": b"hello", "B/deep/x.pdf": b"hello", "B/x copy.pdf": b"hello", "B/._x.pdf": b"hello",
                 "A/l.pdf": b"legal", "Mullins case/l.pdf": b"legal"}
        for rel, body in files.items():
            (self.ssd / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.ssd / rel).write_bytes(body)
        sets = [["A/x.pdf", "B/deep/x.pdf", "B/x copy.pdf", "B/._x.pdf"], ["A/l.pdf", "Mullins case/l.pdf"]]
        report = {"matchSets": [{"fileSize": 5, "fileList": [{"filePath": str(self.ssd / p)} for p in s]} for s in sets]}
        self.report = self.tmp / "jdupes.json"
        self.report.write_text(json.dumps(report))
        self.archive, self.out = self.ssd / "_Dedup-Archive/run1", self.tmp / "run"

    def run_tool(self, *extra):
        r = self.run_py(SCRIPT, "--json", self.report, "--root", self.ssd, "--archive", self.archive, "--out", self.out, *extra)
        with open(self.out / "plan.csv", newline="") as f:
            return r, {row["path"].replace(str(self.ssd) + "/", ""): row["action"] for row in csv.DictReader(f)}

    def test_dry_run_plans_shortest_keeper_flags_legal_and_moves_nothing(self):
        r, plan = self.run_tool()
        self.assertEqual(plan["A/x.pdf"], "keep")
        self.assertEqual(plan["B/deep/x.pdf"], "archive")
        self.assertNotIn("B/._x.pdf", plan)
        self.assertEqual({plan["A/l.pdf"], plan["Mullins case/l.pdf"]}, {"flag-legal"})
        self.assertIn("dry run", r.stdout)
        self.assertTrue((self.ssd / "B/deep/x.pdf").exists())

    def test_apply_moves_verified_copies_and_restore_puts_them_back(self):
        (self.ssd / "B/x copy.pdf").write_bytes(b"HELLO")  # changed after the report: must not move
        r, _ = self.run_tool("--apply")
        self.assertIn("moved 1, skipped 1", r.stdout)
        self.assertTrue((self.archive / "B/deep/x.pdf").exists())
        self.assertFalse((self.ssd / "B/deep/x.pdf").exists())
        self.assertTrue((self.ssd / "Mullins case/l.pdf").exists())
        subprocess.run(["bash", str(self.archive / "restore.sh")], check=True)
        self.assertEqual((self.ssd / "B/deep/x.pdf").read_bytes(), b"hello")
