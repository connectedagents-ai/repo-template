import os, subprocess
from tests.helpers import OPS, TempDirTest

START = OPS / "start.sh"


class StartMenuTest(TempDirTest):
    def choice(self, c):
        env = {**os.environ, "HOME": str(self.tmp)}
        return subprocess.run(["bash", str(START), c], capture_output=True, text=True, env=env)

    def test_setup_check_succeeds_even_when_tools_are_missing(self):
        r = self.choice("1")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("Finished with problems", r.stdout)

    def test_key_finder_choice_passes_through_its_exit_status(self):
        (self.tmp / ".zshrc").write_text("export OPENAI_API_KEY=fake-openai-value-1\n")
        r = self.choice("2")
        self.assertEqual(r.returncode, 0)
        self.assertIn("OPENAI_API_KEY", r.stdout)
