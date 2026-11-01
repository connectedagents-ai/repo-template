import json, subprocess
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
        boundary = (self.root / "memory/BOUNDARY.md").read_text()
        self.assertIn("claude/default tagged ['privileged']", boundary)
        self.assertNotIn("deadline", boundary)

    def test_render_generates_banners_readmes_and_is_stable(self):
        self.built()
        readme = (self.root / "README.md").read_text()
        self.assertTrue(readme.startswith("<!-- GENERATED"))
        self.assertIn("chief-of-staff", readme)
        self.assertIn("Last updated 2099-01-02", readme)
        self.assertIn("Houston", (self.root / "agents/chief-of-staff/memory/MEMORY.md").read_text())
        self.assertIn("Houston", (self.root / "tools/chatgpt/paste.md").read_text())
        self.assertIn("rendered 0 changed files", self.afs("render", "--root", self.root, "--apply").stdout)

    def test_import_agents_converts_codex_toml_and_keeps_existing(self):
        src = self.tmp / "codex-agents"
        src.mkdir()
        (src / "case-analyst.toml").write_text('name = "case-analyst"\ndescription = "Analyzes litigation: case files"\n'
                                               'developer_instructions = """Read the record."""\n')
        (src / "code-reviewer.toml").write_text('name = "code-reviewer"\ndescription = "Reviews diffs"\n')
        (src / "broken.toml").write_text("name = \n")
        self.afs("init", "--root", self.root, "--apply")
        r = self.afs("import-agents", "--root", self.root, "--source", src, "--apply")
        self.assertIn("imported 2 agents", r.stdout)
        legal = (self.root / "agents/case-analyst/AGENT.md").read_text()
        self.assertIn("memory_namespaces: [core, privileged]", legal)
        self.assertIn("Read the record.", legal)
        self.assertIn("[core, engineering]", (self.root / "agents/code-reviewer/AGENT.md").read_text())
        self.assertIn("2 already present", self.afs("import-agents", "--root", self.root, "--source", src, "--apply").stdout)

    def test_restricted_namespace_is_pointer_only(self):
        self.afs("init", "--root", self.root, "--apply")
        f = self.tmp / "fo.md"
        f.write_text("- Trust distribution schedule details\n")
        self.afs("memory", "import", "--root", self.root, "--platform", "claude", "--namespace", "family-office", f, "--apply")
        self.afs("memory", "merge", "--root", self.root, "--apply")
        (entry,) = self.pack()
        self.assertIsNone(entry["body_md"])
        stored = "".join(p.read_text() for p in (self.root / "memory").rglob("*") if p.is_file())
        self.assertNotIn("Trust distribution", stored)
        self.assertIn("[family-office] item", entry["title"])

    def test_privileged_tag_keeps_body_out_of_sources_but_still_dedupes(self):
        self.afs("init", "--root", self.root, "--apply")
        f = self.tmp / "lit.md"
        f.write_text("- Matter deadline is Friday\n- matter deadline is friday.\n")
        r = self.afs("memory", "import", "--root", self.root, "--platform", "claude", "--tag", "privileged", f, "--apply")
        self.assertIn("1 new items", r.stdout)
        src = (self.root / "memory/sources/claude/default.jsonl").read_text()
        self.assertNotIn("deadline", src.lower())
        self.assertIn('"body_hash"', src)

    def test_restated_fact_wins_and_signed_values_stay_distinct(self):
        self.afs("init", "--root", self.root, "--apply")
        rows = [("Location: Austin", "2020"), ("Location: Houston", "2021"), ("Location: Austin", "2022"),
                ("Balance: -100", "2020"), ("Balance: 100", "2020")]
        for n, (body, year) in enumerate(rows):
            f = self.tmp / f"m{n}.jsonl"
            f.write_text(json.dumps({"body_md": body, "key": body.split(":")[0].lower(), "updated_at": f"{year}-01-01T00:00:00Z"}) + "\n")
            self.afs("memory", "import", "--root", self.root, "--platform", "grok", "--account", "x", f, "--apply")
        self.afs("memory", "merge", "--root", self.root, "--apply")
        live = {e["key"]: e["body_md"] for e in self.pack()}
        self.assertEqual(live["location"], "Location: Austin")
        src = (self.root / "memory/sources/grok/x.jsonl").read_text()
        self.assertIn("Balance: -100", src)
        self.assertIn("Balance: 100", src)

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

    def test_refresh_dry_run_previews_merged_files_without_changing_the_repo(self):
        self.afs("init", "--root", self.root, "--apply")
        f = self.tmp / "m.md"
        f.write_text("- Location: Austin\n")
        self.afs("memory", "import", "--root", self.root, "--platform", "chatgpt", f, "--apply")
        r = subprocess.run(["bash", str(AFS.parent / "refresh.sh"), "--root", str(self.root)], capture_output=True, text=True,
                           env={**__import__("os").environ, **self.env}, check=True)
        self.assertIn("DRY RUN", r.stdout)
        self.assertIn("would", r.stdout)
        self.assertFalse((self.root / "memory/pack.jsonl").exists())
        self.assertFalse((self.home / ".codex").exists())

    def test_import_scrubs_restricted_bodies_left_by_older_versions(self):
        self.afs("init", "--root", self.root, "--apply")
        dest = self.root / "memory/sources/claude/default.jsonl"
        dest.parent.mkdir(parents=True)
        dest.write_text(json.dumps({"platform": "claude", "account": "default", "item_id": "x", "title": "Secret plan",
                                    "body_md": "Secret plan", "updated_at": "2020-01-01T00:00:00Z", "tags": [],
                                    "provenance_hash": "a" * 32, "namespace": "privileged", "source_url": "s"}) + "\n")
        empty = self.tmp / "none.md"
        empty.write_text("")
        r = self.afs("memory", "import", "--root", self.root, "--platform", "claude", empty, "--apply")
        self.assertIn("1 restricted bodies removed", r.stdout)
        self.assertNotIn("Secret", dest.read_text())

    def test_pointer_and_inlined_copies_of_a_restricted_fact_merge_into_one(self):
        self.afs("init", "--root", self.root, "--apply")
        f = self.tmp / "fo.md"
        f.write_text("- Trust distribution schedule\n")
        self.afs("memory", "import", "--root", self.root, "--platform", "claude", "--namespace", "family-office", f, "--apply")
        legacy = self.root / "memory/sources/grok/old.jsonl"
        legacy.parent.mkdir(parents=True)
        legacy.write_text(json.dumps({"platform": "grok", "account": "old", "title": "Trust distribution schedule",
                                      "body_md": "Trust distribution schedule", "updated_at": "2020-01-01T00:00:00Z",
                                      "tags": [], "provenance_hash": "b" * 32, "namespace": "family-office",
                                      "source_url": "s"}) + "\n")
        self.afs("memory", "merge", "--root", self.root, "--apply")
        (entry,) = self.pack()
        self.assertEqual({s["platform"] for s in entry["sources"]}, {"claude", "grok"})
        self.assertNotIn("Trust", json.dumps(entry))

    def test_fact_reimported_as_privileged_is_reclassified_and_scrubbed(self):
        self.afs("init", "--root", self.root, "--apply")
        f = self.tmp / "m.md"
        f.write_text("- Settlement figure is high\n")
        self.afs("memory", "import", "--root", self.root, "--platform", "claude", f, "--apply")
        r = self.afs("memory", "import", "--root", self.root, "--platform", "claude", "--tag", "privileged", f, "--apply")
        self.assertIn("1 reclassified as restricted", r.stdout)
        self.afs("memory", "merge", "--root", self.root, "--apply")
        self.assertNotIn("Settlement", (self.root / "memory/sources/claude/default.jsonl").read_text())
        self.assertNotIn("Settlement", json.dumps(self.pack()))

    def test_pointer_records_survive_export_to_another_agent_home(self):
        self.afs("init", "--root", self.root, "--apply")
        f = self.tmp / "fo.md"
        f.write_text("- Trust schedule\n")
        self.afs("memory", "import", "--root", self.root, "--platform", "claude", "--namespace", "family-office", f, "--apply")
        other = self.tmp / "other-home"
        self.afs("init", "--root", other, "--apply")
        r = self.afs("memory", "import", "--root", other, "--platform", "claude",
                     self.root / "memory/sources/claude/default.jsonl", "--apply")
        self.assertIn("1 new items", r.stdout)
        moved = (other / "memory/sources/claude/default.jsonl").read_text()
        self.assertIn('"body_hash"', moved)
        self.assertNotIn("Trust", moved)

    def test_sync_preview_from_a_copy_compares_against_the_real_home(self):
        self.built()
        self.afs("sync", "--root", self.root, "--apply")
        r = self.afs("sync", "--root", self.root, "--source-root", self.root)
        self.assertIn("ok     claude", r.stdout)

    def test_keyed_conflict_between_pointers_keeps_the_newest(self):
        self.afs("init", "--root", self.root, "--apply")
        for n, (body, year) in enumerate([("Trustee: Alpha", "2020"), ("Trustee: Beta", "2021")]):
            f = self.tmp / f"t{n}.jsonl"
            f.write_text(json.dumps({"body_md": body, "key": "trustee", "updated_at": f"{year}-01-01T00:00:00Z"}) + "\n")
            self.afs("memory", "import", "--root", self.root, "--platform", "grok", "--namespace", "family-office", f, "--apply")
        self.afs("memory", "merge", "--root", self.root, "--apply")
        (entry,) = self.pack()
        self.assertEqual(entry["updated_at"][:4], "2021")
        self.assertNotIn("Alpha", (self.root / "memory/CONFLICTS.md").read_text())
