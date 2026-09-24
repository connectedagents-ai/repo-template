import subprocess
from tests.helpers import OPS, TempDirTest

FIND = OPS / "secrets/find_plaintext_keys.py"


class FindPlaintextKeysTest(TempDirTest):
    def test_reports_names_only_and_ignores_references_and_examples(self):
        repo = self.tmp / "cfg"
        repo.mkdir()
        (repo / ".zshrc").write_text('export OPENAI_API_KEY=fake-openai-value-1\n'
                                     'export ANTHROPIC_API_KEY="$(op read op://AI/anthropic/key)"\n'
                                     'GH_TOKEN=op://AI/github/token\n')
        (repo / "settings.json").write_text('{\n  "apiKey": "fake-xai-value-3"\n}\n')
        (repo / ".env.example").write_text("STRIPE_SECRET_KEY=fake-stripe-value-2\n")
        r = self.run_py(FIND, "--no-defaults", repo)
        self.assertIn("OPENAI_API_KEY", r.stdout)
        self.assertIn("apiKey", r.stdout)
        for absent in ("ANTHROPIC_API_KEY", "GH_TOKEN", "STRIPE_SECRET_KEY", "fake-openai-value-1", "fake-xai-value-3"):
            self.assertNotIn(absent, r.stdout)

    def test_committed_key_is_flagged_and_exits_nonzero(self):
        repo = self.tmp / "repo"
        repo.mkdir()
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        (repo / ".env").write_text("XAI_API_KEY=fake-xai-value-4\n")
        subprocess.run(["git", "-C", str(repo), "add", ".env"], check=True)
        r = self.run_py(FIND, "--no-defaults", repo, check=False)
        self.assertEqual(r.returncode, 1)
        self.assertIn("COMMITTED TO GIT", r.stdout)
