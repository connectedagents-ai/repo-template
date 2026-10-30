import csv
from tests.helpers import OPS, TempDirTest

HUB = OPS / "skills/skills_hub.py"


def skill(folder, name, body="Do the thing.", description="Use when testing."):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "SKILL.md").write_text(f"---\nname: {name}\ndescription: {description}\n---\n{body}\n")


class SkillsHubTest(TempDirTest):
    def setUp(self):
        super().setUp()
        self.home = self.tmp / "home"
        self.env = {"HOME": str(self.home)}

    def test_inventory_groups_copies_and_flags_bad_front_matter(self):
        skill(self.home / ".claude/skills/deploy", "deploy")
        skill(self.home / ".agents/skills/deploy", "deploy")
        skill(self.home / ".cursor/skills/review", "review", body="v1")
        skill(self.home / ".codex/skills/review", "review", body="v2")
        skill(self.home / ".grok/skills/Bad_Name", "Bad_Name", description="")
        out = self.tmp / "skills.csv"
        r = self.run_py(HUB, "inventory", "--out", out, env=self.env)
        with out.open() as f:
            rows = {(row["name"], row["tool"]): row for row in csv.DictReader(f)}
        self.assertEqual(rows[("deploy", "agents")]["duplicate"].split()[0], "identical")
        self.assertEqual(rows[("review", "codex")]["duplicate"], "variant: merge")
        self.assertIn("no description", rows[("Bad_Name", "grok")]["issues"])
        self.assertIn("not kebab-case", rows[("Bad_Name", "grok")]["issues"])
        self.assertIn("5 skills, 3 distinct names, 2 names with more than one copy", r.stdout)

    def test_inventory_scans_repo_level_skill_folders(self):
        skill(self.tmp / "code/app/.claude/skills/ship", "ship")
        skill(self.tmp / "code/app/node_modules/pkg/.claude/skills/noise", "noise")
        r = self.run_py(HUB, "inventory", "--scan-repos", self.tmp / "code", env=self.env)
        self.assertIn("ship", r.stdout)
        self.assertNotIn("noise", r.stdout)

    def test_link_dry_run_changes_nothing(self):
        skill(self.tmp / "hub/deploy", "deploy")
        r = self.run_py(HUB, "link", "--hub", self.tmp / "hub", env=self.env)
        self.assertIn("DRY RUN", r.stdout)
        self.assertFalse((self.home / ".claude").exists())

    def test_link_apply_archives_existing_copy_and_is_reversible(self):
        skill(self.tmp / "hub/deploy", "deploy", body="canonical")
        skill(self.home / ".claude/skills/deploy", "deploy", body="old local copy")
        self.run_py(HUB, "link", "--hub", self.tmp / "hub", "--target", ".claude/skills", "--apply", env=self.env)
        dest = self.home / ".claude/skills/deploy"
        self.assertTrue(dest.is_symlink())
        self.assertIn("canonical", (dest / "SKILL.md").read_text())
        (archive,) = (self.home / "Archive").glob("skills-replaced-*")
        self.assertIn("old local copy", next(archive.rglob("SKILL.md")).read_text())
        self.assertTrue((archive / "restore.sh").exists())
        again = self.run_py(HUB, "link", "--hub", self.tmp / "hub", "--target", ".claude/skills", env=self.env)
        self.assertIn("nothing to do", again.stdout)
