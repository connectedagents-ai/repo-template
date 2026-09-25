import os, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OPS = ROOT / "ops"


class TempDirTest(unittest.TestCase):
    """Each test gets a fresh temp dir outside the repo (some scripts refuse to write inside a git work tree)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def run_py(self, script, *args, check=True, env=None):
        r = subprocess.run([sys.executable, str(script), *map(str, args)], capture_output=True, text=True,
                           env={**os.environ, **(env or {})})
        if check and r.returncode != 0:
            self.fail(f"{script.name} exited {r.returncode}\nstdout:\n{r.stdout}\nstderr:\n{r.stderr}")
        return r
