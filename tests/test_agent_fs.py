import json
from tests.helpers import OPS, TempDirTest

AFS = OPS / "agents/agent_fs.py"


class AgentFsTest(TempDirTest):
    def setUp(self):
        super().setUp()
        self.root, self.home = self.tmp / "home-repo", self.tmp / "home"
        self.home.mkdir()
        self.env = {"HOME": str(self.home)}

    def afs(self, *args, check=True):
        return self.run_py(AFS, *args, env=self.env, check=check)

    def built(self):
        self.afs("init", "--root", self.root, "--apply")
        a, b = self.tmp / "chatgpt.md", self.tmp / "grok.jsonl"
        a.write_text("# Memories\n- Location: Austin\n- Prefers short answers\n- Case strategy notes\n")
        b.write_text(json.dumps({"body_md": "Location: Houston", "key": "location", "updated_at": "2099-01-01T00:00:00Z"}) + "\n" +
                     json.dumps({"body_md": "prefers  SHORT answers!", "updated_at": "2099-01-02T00:00:00Z"}) + "\n")
        self.afs("memory", "import", "--root", self.root, "--platform", "chatgpt", "--account", "personal", a, "--apply")
        self.afs("memory", "import", "--root", self.root, "--platform", "grok", "--account", "x", b, "--apply")
        lit = self.tmp / "lit.md"
        lit.write_text("- Matter deadline is Friday\n")
        self.afs("memory", "import", "--root", self.root, "--platform", "claude", "--namespace", "core", "--tag", "privileged", lit, "--apply")
        self.afs("memory", "merge", "--root", self.root, "--apply")
        self.afs("render", "--root", self.root, "--apply")

    def pack(self):
        return [json.loads(ln) for ln in (self.root / "memory/pack.jsonl").read_text().splitlines()]

    def test_init_is_dry_by_default_and_idempotent(self):
        r = self.afs("init", "--root", self.root)
        self.assertIn("would create", r.stdout)
        self.assertFalse(self.root.exists())
        self.afs("init", "--root", self.root, "--apply")
        self.assertTrue((self.root / "agents/chief-of-staff/AGENT.md").exists())
        self.assertIn("created 0 files", self.afs("init", "--root", self.root, "--apply").stdout)

    def test_merge_dedupes_across_platforms_resolves_conflicts_and_enforces_boundary(self):
        self.built()
        pack = self.pack()
        short = [e for e in pack if "short answers" in e["body_md"].lower()]
        self.assertEqual(len(short), 1)
        self.assertEqual({s["platform"] for s in short[0]["sources"]}, {"chatgpt", "grok"})
        locations = [e["body_md"] for e in pack if e.get("key") == "location"]
        self.assertEqual(locations, ["Location: Houston"])
        self.assertIn("Austin", (self.root / "memory/CONFLICTS.md").read_text())
        self.assertNotIn("deadline", json.dumps(pack))
        self.assertIn("Matter deadline", (self.root / "memory/BOUNDARY.md").read_text())

    def test_render_generates_banners_readmes_and_is_stable(self):
        self.built()
        readme = (self.root / "README.md").read_text()
        self.assertTrue(readme.startswith("<!-- GENERATED"))
        self.assertIn("chief-of-staff", readme)
        self.assertIn("Houston", (self.root / "agents/chief-of-staff/memory/MEMORY.md").read_text())
        self.assertIn("Houston", (self.root / "tools/chatgpt/paste.md").read_text())
        self.assertIn("rendered 0 changed files", self.afs("render", "--root", self.root, "--apply").stdout)

    def test_restricted_namespace_is_pointer_only(self):
        self.afs("init", "--root", self.root, "--apply")
        f = self.tmp / "fo.md"
        f.write_text("- Trust distribution schedule details\n")
        self.afs("memory", "import", "--root", self.root, "--platform", "claude", "--namespace", "family-office", f, "--apply")
        self.afs("memory", "merge", "--root", self.root, "--apply")
        (entry,) = self.pack()
        self.assertIsNone(entry["body_md"])

    def test_sync_dry_run_then_apply_backs_up_and_keeps_user_content(self):
        self.built()
        codex = self.home / ".codex/AGENTS.md"
        codex.parent.mkdir()
        codex.write_text("my own rules\n")
        r = self.afs("sync", "--root", self.root)
        self.assertIn("would update", r.stdout)
        self.assertEqual(codex.read_text(), "my own rules\n")
        self.afs("sync", "--root", self.root, "--apply")
        text = codex.read_text()
        self.assertIn("my own rules", text)
        self.assertIn("<!-- agent-home:start -->", text)
        self.assertIn("@", (self.home / ".claude/CLAUDE.md").read_text())
        (restore,) = (self.home / "Archive").glob("agent-home-sync-*/restore.sh")
        self.assertIn(".codex/AGENTS.md", restore.read_text())
        self.assertIn("ok", self.afs("sync", "--root", self.root, "--apply").stdout)
