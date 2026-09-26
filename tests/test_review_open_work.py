import os, stat, subprocess
from tests.helpers import OPS, TempDirTest

SCRIPT = OPS / "github-consolidation/review_open_work.sh"

FAKE_GH = r'''#!/bin/bash
case "$*" in
  "repo list"*) printf 'busy\tfalse\tfalse\t2026-09-01T00:00:00Z\tmain\nquiet\tfalse\tfalse\t2026-05-01T00:00:00Z\tmain\nbroken\tfalse\tfalse\t2026-05-01T00:00:00Z\tmain\n' ;;
  "pr list -R acme/busy"*) echo 2 ;;
  "pr list -R acme/broken"*) exit 1 ;;
  "pr list"*) echo 0 ;;
  "api repos/acme/busy/branches"*) printf 'main\nfeat/x\nold/merged\n' ;;
  "api repos/acme/busy/compare/main...feat/x"*) echo 3 ;;
  "api repos/acme/busy/compare/main...old/merged"*) echo 0 ;;
  "api repos/acme/"*"/branches"*) echo main ;;
  *) exit 1 ;;
esac
'''


class ReviewOpenWorkTest(TempDirTest):
    def run_script(self):
        b = self.tmp / "bin"
        b.mkdir(exist_ok=True)
        gh = b / "gh"
        gh.write_text(FAKE_GH)
        gh.chmod(gh.stat().st_mode | stat.S_IEXEC)
        out = self.tmp / "work.csv"
        r = subprocess.run(["bash", str(SCRIPT), "acme"], capture_output=True, text=True, cwd=self.tmp,
                           env={**os.environ, "PATH": f"{b}:/usr/bin:/bin", "OUT": str(out)})
        return r, out.read_text()

    def test_lists_open_prs_and_only_branches_with_unmerged_commits(self):
        r, csv = self.run_script()
        self.assertIn('busy,false,false,2026-09-01T00:00:00Z,main,2,1,"feat/x(+3)"', csv)
        self.assertIn('quiet,false,false,2026-05-01T00:00:00Z,main,0,0,""', csv)
        self.assertIn("busy", r.stdout)
        self.assertNotIn("quiet ", r.stdout)

    def test_a_repo_that_cannot_be_checked_fails_the_run(self):
        r, csv = self.run_script()
        self.assertEqual(r.returncode, 1)
        self.assertIn("broken,false,false,2026-05-01T00:00:00Z,main,?,", csv)
