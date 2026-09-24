import json, subprocess, zipfile
from tests.helpers import OPS, TempDirTest

INGEST = OPS / "ai-library/ingest_library.py"


def chatgpt_export(convs):
    return json.dumps([{"id": cid, "title": title, "create_time": 1700000000,
                        "mapping": {"a": {"message": {"author": {"role": "user"}, "create_time": 1,
                                                      "content": {"parts": [text]}}}}} for cid, title, text in convs])


class IngestLibraryTest(TempDirTest):
    def setUp(self):
        super().setUp()
        self.lib = self.tmp / "lib"
        self.exp = self.tmp / "export"

    def ingest(self, *inputs, source="chatgpt", account="personal"):
        return self.run_py(INGEST, "--source", source, "--account", account, "--library", self.lib,
                           "--min-free-gb", 0, "--apply", *inputs)

    def catalog(self):
        return json.loads((self.lib / "catalog.json").read_text(encoding="utf-8"))

    def test_skill_copy_skips_secrets_and_symlinks(self):
        skill = self.exp / "my-skill"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text("---\nname: my-skill\n---\n")
        (skill / ".env").write_text("KEY=1")
        (skill / "api_token.txt").write_text("t")
        (skill / "link").symlink_to("/etc/hosts")
        self.ingest(self.exp)
        copied = {p.name for p in (self.lib / "skills/my-skill").iterdir()}
        self.assertEqual(copied, {"SKILL.md"})

    def test_identical_skill_from_second_account_is_a_duplicate_with_provenance(self):
        for acct in ("personal", "team"):
            skill = self.tmp / acct / "writer"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("same")
            self.ingest(self.tmp / acct, account=acct)
        self.assertEqual([p.name for p in (self.lib / "skills").iterdir()], ["writer"])
        (entry,) = [e for e in self.catalog().values() if e["kind"] == "skill"]
        self.assertEqual({o["account"] for o in entry["origins"]}, {"personal", "team"})

    def test_numbered_chatgpt_files_are_split_and_reingest_replaces_by_id(self):
        self.exp.mkdir()
        (self.exp / "conversations-001.json").write_text(chatgpt_export([("abc", "Old title", "hello")]), encoding="utf-8")
        self.ingest(self.exp)
        (self.exp / "conversations-001.json").write_text(chatgpt_export([("abc", "New title", "héllo ✓")]), encoding="utf-8")
        self.ingest(self.exp)
        chats = list((self.lib / "sources/chatgpt/personal/chats").glob("*.md"))
        self.assertEqual(len(chats), 1)
        self.assertIn("New-title", chats[0].name)
        self.assertIn("héllo ✓", chats[0].read_text(encoding="utf-8"))

    def test_zip_larger_than_free_space_is_refused(self):
        z = self.tmp / "export.zip"
        with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as f:
            f.writestr("big.txt", "0" * 10_000_000)
        r = self.run_py(INGEST, "--source", "chatgpt", "--library", self.lib, "--min-free-gb", 10**6, z, check=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("STOP", r.stderr)
        self.assertEqual(list(self.tmp.glob(".ingest-*")), [])

    def test_refuses_library_inside_git_work_tree(self):
        subprocess.run(["git", "init", "-q", str(self.tmp / "repo")], check=True)
        self.exp.mkdir()
        r = self.run_py(INGEST, "--source", "x", "--library", self.tmp / "repo/lib", self.exp, check=False)
        self.assertIn("refusing", r.stderr)
