import os, stat, subprocess
from tests.helpers import OPS, TempDirTest

SCRIPT = OPS / "cowork/bootstrap_mac.sh"
READY = ["git", "gh", "node", "python3", "claude", "brew", "op"]  # pnpm, uv, jq, rclone left missing


class BootstrapMacTest(TempDirTest):
    def setUp(self):
        super().setUp()
        self.bin, self.home = self.tmp / "bin", self.tmp / "home"
        self.bin.mkdir()
        self.home.mkdir()
        for name in READY:
            body = '#!/bin/bash\necho "$0 $@" >> "$HOME/calls.log"\n'
            if name == "gh":
                body += '[ "$1 $2" = "auth status" ] && exit 1\n'
            p = self.bin / name
            p.write_text(body + "exit 0\n")
            p.chmod(p.stat().st_mode | stat.S_IEXEC)

    def run_script(self, *args):
        env = {**os.environ, "HOME": str(self.home), "PATH": f"{self.bin}:/usr/bin:/bin", "SSD": str(self.tmp / "no-ssd")}
        return subprocess.run(["bash", str(SCRIPT), *args], capture_output=True, text=True, env=env, check=True)

    def test_preview_lists_missing_and_owner_steps_and_changes_nothing(self):
        out = self.run_script().stdout
        self.assertIn("READY     git", out)
        self.assertIn("MISSING   pnpm  (fix: brew install pnpm)", out)
        self.assertIn("NEEDS YOU gh login", out)
        self.assertIn("NEEDS YOU plug in the SSD", out)
        self.assertIn("Preview only: nothing changed", out)
        self.assertFalse((self.home / ".claude/CLAUDE.md").exists())
        self.assertNotIn("brew install", (self.home / "calls.log").read_text())

    def test_apply_installs_missing_and_rules_keeping_a_backup(self):
        (self.home / ".claude").mkdir()
        (self.home / ".claude/CLAUDE.md").write_text("old rules\n")
        out = self.run_script("--apply").stdout
        calls = (self.home / "calls.log").read_text()
        self.assertIn("brew install pnpm", calls)
        self.assertIn("brew install uv", calls)
        self.assertIn("INSTALLED", out)
        self.assertIn("Global instructions", (self.home / ".claude/CLAUDE.md").read_text())
        backups = list((self.home / ".claude").glob("CLAUDE.md.bak-*"))
        self.assertEqual([b.read_text() for b in backups], ["old rules\n"])
        codex = (self.home / ".codex/AGENTS.md").read_text()
        self.assertIn("## 6. Agent-run jobs", codex)
        self.assertIn("## 7. Standing authority", codex)
