import os, stat, subprocess
from tests.helpers import OPS, TempDirTest

SCAN = OPS / "security/scan_infected_repos.sh"
BAD = "cnVuOiBlY2hvIGhpIHwgYmFzZTY0IC1kIHwgYmFzaAo="   # base64 of: run: echo hi | base64 -d | bash
GOOD = "cnVuOiBtYWtlIHRlc3QK"                          # base64 of: run: make test

FAKE_GH = r'''#!/bin/bash
case "$*" in
  "repo list acme"*) printf 'hit\nold\nclean\n' ;;
  *"repos/acme/old/commits"*) echo 2 ;;
  *"commits"*) echo 0 ;;
  *"repos/acme/hit/contents/.github/workflows -q"*) echo ci.yml ;;
  *"repos/acme/clean/contents/.github/workflows -q"*) echo ci.yml ;;
  *"repos/acme/hit/contents/.github/workflows/ci.yml"*) echo "$BAD" ;;
  *"repos/acme/clean/contents/.github/workflows/ci.yml"*) echo "$GOOD" ;;
  *) exit 1 ;;
esac
'''


class ScanInfectedReposTest(TempDirTest):
    def test_flags_bad_workflows_and_build_bot_commits_only(self):
        b = self.tmp / "bin"
        b.mkdir()
        gh = b / "gh"
        gh.write_text(FAKE_GH)
        gh.chmod(gh.stat().st_mode | stat.S_IEXEC)
        out = self.tmp / "scan.txt"
        env = {**os.environ, "PATH": f"{b}:/usr/bin:/bin", "OUT": str(out), "BAD": BAD, "GOOD": GOOD}
        subprocess.run(["bash", str(SCAN), "acme"], capture_output=True, text=True, env=env, check=True)
        text = out.read_text()
        self.assertIn("INFECTED  acme/hit  build-bot commits: 0  bad workflows: ci.yml", text)
        self.assertIn("INFECTED  acme/old  build-bot commits: 2", text)
        self.assertNotIn("acme/clean", text)
        self.assertIn("scan finished: 2 infected repo(s)", text)
