import csv, os, subprocess, zipfile
from tests.helpers import OPS, TempDirTest

SCRIPT = OPS / "financial-discovery/find_financial_records.py"


class FindFinancialRecordsTest(TempDirTest):
    def setUp(self):
        super().setUp()
        self.src = self.tmp / "files"
        (self.src / "taxes").mkdir(parents=True)
        (self.src / "bank").mkdir()
        (self.src / "bank/statement.txt").write_text("Chase checking account statement period 03/2023 ending balance")
        (self.src / "bank/copy.txt").write_text("Chase checking account statement period 03/2023 ending balance")
        (self.src / "taxes/2021_1040.txt").write_text("Form 1040 tax return 2021")
        with zipfile.ZipFile(self.src / "fund.docx", "w") as z:
            z.writestr("word/document.xml", "<w:t>Schedule K-1 limited partnership capital account 2024</w:t>")
        (self.src / "memo.txt").write_text("Privileged attorney-client advice about the brokerage account 2023")
        (self.src / "recipe.txt").write_text("Soup with carrots, 2023")
        nc = self.src / "Library/CloudStorage/GoogleDrive-me/Shared drives/Non Circumvent NDA Acme Roofing copy"
        nc.mkdir(parents=True)
        (nc / "signed 2024.txt").write_text("brokerage")
        (self.src / "Library/Caches").mkdir(parents=True)
        (self.src / "Library/Caches/bank statement 2024.txt").write_text("app cache")
        self.out = self.tmp / "out"

    def run_script(self, *extra):
        return self.run_py(SCRIPT, "--out", self.out, "--allow-internal", *extra, self.src)

    def rows(self):
        with open(self.out / "index.csv") as f:
            return {os.path.basename(r["path"]): r for r in csv.DictReader(f)}

    def test_preview_indexes_financial_records_since_2022_and_copies_nothing(self):
        r = self.run_script()
        rows = self.rows()
        self.assertEqual(rows["statement.txt"]["category"], "banking")
        self.assertEqual(rows["statement.txt"]["years"], "2023")
        self.assertEqual(rows["fund.docx"]["category"], "lp-business-interests")
        self.assertEqual(rows["copy.txt"]["duplicate_of"], str(self.src / "bank/statement.txt"))
        self.assertEqual(rows["memo.txt"]["privilege_review"], "yes")
        self.assertNotIn("2021_1040.txt", rows)
        self.assertNotIn("recipe.txt", rows)
        self.assertFalse((self.out / "collection").exists())
        self.assertIn("Preview only", r.stdout)

    def test_apply_copies_unique_matches_with_clean_names_and_keeps_originals(self):
        self.run_script("--apply")
        col = self.out / "collection"
        self.assertTrue((col / "banking/2023/2023_banking_statement.txt").is_file())
        self.assertTrue((col / "lp-business-interests/2024/2024_lp-business-interests_fund.docx").is_file())
        self.assertEqual(len(list((col / "_privilege-review").iterdir())), 1)
        self.assertEqual(len(list((col / "banking/2023").iterdir())), 1)
        self.assertTrue((self.src / "bank/statement.txt").is_file())
        self.assertEqual(len((self.out / "COPIED.tsv").read_text().splitlines()), 4)

    def test_agreements_by_folder_name_even_under_a_library_folder(self):
        self.run_script()
        row = self.rows()["signed 2024.txt"]
        self.assertEqual(row["category"], "agreements")
        self.assertEqual(row["text_read"], "name-only")
        self.assertEqual(row["years"], "2024")
        self.assertNotIn("bank statement 2024.txt", self.rows())

    def test_refuses_internal_disk_without_flag(self):
        r = self.run_py(SCRIPT, "--out", self.out, self.src, check=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("external drive", r.stderr)

    def test_local_terms_file_adds_matter_words(self):
        terms = self.tmp / "terms.txt"
        terms.write_text("banking: soup\n")
        self.run_script("--terms", terms)
        self.assertEqual(self.rows()["recipe.txt"]["category"], "banking")

    def test_entities_file_tags_and_files_by_company(self):
        ents = self.tmp / "entities.txt"
        ents.write_text("Acme Holdings LLC: acme\s*holdings|12-?3456789\nBeta Fund LP: beta\s*fund\n")
        (self.src / "bank/acme.txt").write_text("Chase checking statement 2024 EIN 12-3456789")
        self.run_script("--entities", ents, "--apply")
        self.assertEqual(self.rows()["acme.txt"]["entities"], "Acme Holdings LLC")
        self.assertTrue((self.out / "collection/Acme Holdings LLC/banking/2024/2024_banking_acme.txt").is_file())
        self.assertTrue((self.out / "collection/_no-entity/banking/2023/2023_banking_statement.txt").is_file())

    def test_move_duplicates_preview_then_apply_and_restore(self):
        dup, keep = self.src / "bank/copy.txt", self.src / "bank/statement.txt"
        r = self.run_script("--move-duplicates")
        self.assertIn("Would move 1 duplicates", r.stdout)
        self.assertTrue(dup.is_file())
        self.run_script("--move-duplicates", "--apply")
        moved = self.src / "_duplicates/bank/copy.txt"
        self.assertTrue(moved.is_file())
        self.assertFalse(dup.exists())
        self.assertTrue(keep.is_file())
        subprocess.run(["bash", str(self.out / "restore_duplicates.sh")], check=True)
        self.assertTrue(dup.is_file())
        self.assertFalse(moved.exists())

    def test_cloud_duplicate_stays_inside_its_shared_drive(self):
        drive = self.src / "Library/CloudStorage/GoogleDrive-me/Shared drives/Deals"
        (drive / "a").mkdir(parents=True)
        (drive / "b").mkdir()
        (drive / "a/bank statement 2024.pdf").write_text("x")
        (drive / "b/bank statement 2024 copy.pdf").write_text("x")
        self.run_script("--move-duplicates", "--apply")
        self.assertTrue((drive / "_duplicates/b/bank statement 2024 copy.pdf").is_file())
        self.assertTrue((drive / "a/bank statement 2024.pdf").is_file())

    def test_litigation_categories_and_type_layout(self):
        cats = OPS / "financial-discovery/litigation_categories.txt"
        ents = self.tmp / "entities.txt"
        ents.write_text("Acme Corp: acme\n")
        (self.src / "Acme MNDA signed 2022.pdf").write_text("x")
        (self.src / "deposition outline acme 2024.docx").write_text("outline")
        self.run_script("--categories", cats, "--entities", ents, "--layout", "type", "--since", "2021", "--apply")
        rows = self.rows()
        self.assertEqual(rows["Acme MNDA signed 2022.pdf"]["category"], "02-agreements")
        self.assertEqual(rows["Acme MNDA signed 2022.pdf"]["entities"], "Acme Corp")
        col = self.out / "collection"
        self.assertTrue((col / "02-agreements/2022/2022_02-agreements_Acme MNDA signed 2022.pdf").is_file())
        self.assertTrue((col / "10-deposition-prep/2024").is_dir())

