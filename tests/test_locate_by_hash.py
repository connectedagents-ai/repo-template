import csv, hashlib
from tests.helpers import OPS, TempDirTest

LOCATE = OPS / "dedup/locate_by_hash.py"


def sha(b):
    return hashlib.sha256(b).hexdigest()


class LocateByHashTest(TempDirTest):
    def setUp(self):
        super().setUp()
        self.root = self.tmp / "mac"
        for rel, body in {"Desktop/Sorted/ledger.pdf": b"ledger v1", "Archive/collapse/ledger.pdf": b"ledger v1",
                          "Documents/memo.docx": b"memo", "Documents/other.txt": b"unrelated!",
                          "Code/app/node_modules/x/ledger.pdf": b"ledger v1",
                          "Desktop/.memo.docx.icloud": b"placeholder"}.items():
            (self.root / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.root / rel).write_bytes(body)

    def locate(self, listing, *extra):
        out = self.tmp / "out"
        r = self.run_py(LOCATE, "--hashes", listing, "--root", self.root, "--out", out, *extra)
        with open(out / "located.csv", newline="") as f:
            located = {row["hash"]: row for row in csv.DictReader(f)}
        with open(out / "missing.csv", newline="") as f:
            missing = [row["hash"] for row in csv.DictReader(f)]
        return r, located, missing

    def test_finds_moved_files_lists_every_copy_and_reports_missing(self):
        listing = self.tmp / "release.csv"
        listing.write_text("sha256,size,old_path\n"
                           f"{sha(b'ledger v1')},9,/Users/r/Desktop/ledger.pdf\n"
                           f"{sha(b'memo')},4,/Users/r/Desktop/memo.docx\n"
                           f"{sha(b'gone')},4,/Users/r/Desktop/gone.pdf\n")
        r, located, missing = self.locate(listing)
        ledger = located[sha(b"ledger v1")]
        self.assertEqual(ledger["copies"], "2")  # node_modules copy is skipped
        self.assertIn("Archive/collapse/ledger.pdf", ledger["all_paths"])
        self.assertTrue(located[sha(b"memo")]["current_path"].endswith("Documents/memo.docx"))
        self.assertEqual(missing, [sha(b"gone")])
        self.assertIn("located 2 of 3 (66%)", r.stdout)

    def test_size_prefilter_hashes_only_matching_sizes(self):
        listing = self.tmp / "release.csv"
        listing.write_text(f"hash,size\n{sha(b'memo')},4\n")
        r, located, _ = self.locate(listing)
        self.assertIn("hashed 1 candidate files", r.stdout)
        self.assertEqual(len(located), 1)

    def test_plain_md5_list_is_detected(self):
        listing = self.tmp / "hashes.txt"
        listing.write_text(hashlib.md5(b"memo").hexdigest().upper() + "\nnot-a-hash\n")
        r, located, _ = self.locate(listing)
        (row,) = located.values()
        self.assertEqual(row["algo"], "md5")
        self.assertIn("located 1 of 1", r.stdout)
