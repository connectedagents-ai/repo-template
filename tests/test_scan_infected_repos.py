import os, stat, subprocess
from tests.helpers import OPS, TempDirTest

SCAN = OPS / "security/scan_infected_repos.sh"
BAD = "cnVuOiBlY2hvIGhpIHwgYmFzZTY0IC1kIHwgYmFzaAo="   # base64 of: run: echo hi | base64 -d | bash
GOOD = "cnVuOiBtYWtlIHRlc3QK"                          # base64 of: run: make test

# Fake gh. HTTP errors print the API's JSON to stdout and exit 1, as the real gh does.
FAKE_GH = r'''#!/bin/bash
case "$*" in
  "repo list acme"*) printf 'hit\nold\nclean\nempty\nlocked\nwfdenied\n' ;;
  "repo list ghost"*) echo "HTTP 401: Bad credentials" >&2; exit 1 ;;
  *"repos/acme/empty/branches"*) echo '{"message":"Git Repository is empty.","status":"409"}'; exit 1 ;;
  *"repos/acme/locked/branches"*) echo '{"message":"Forbidden","status":"403"}'; exit 1 ;;
  *"--paginate repos/acme/hit/branches"*) printf 'main\nmega-1\n' ;;
  *"repos/acme/hit/branches"*) echo main ;;
  *"ref=main repos/acme/wfdenied/contents/.github/workflows -q"*) echo '{"message":"API rate limit exceeded","status":"403"}'; exit 1 ;;
  *"branches"*) echo main ;;
  *"sha=main -f author=ci-bot@automated.dev -f per_page=10 repos/acme/old/commits"*) echo 2 ;;
  *"commits"*) echo 0 ;;
  *"ref=mega-1 repos/acme/hit/contents/.github/workflows -q"*) printf 'megalodon.yml\nsecurity audit.yml\n' ;;
  *"ref=mega-1 repos/acme/hit/contents/.github/workflows/megalodon.yml"*) echo "$BAD" ;;
  *"ref=mega-1 repos/acme/hit/contents/.github/workflows/security%20audit.yml"*) echo "$BAD" ;;
  *"ref=main repos/acme/clean/contents/.github/workflows -q"*) echo ci.yml ;;
  *"repos/acme/clean/contents/.github/workflows/ci.yml"*) echo "$GOOD" ;;
  *) echo '{"message":"Not Found","status":"404"}'; exit 1 ;;
esac
'''


class ScanInfectedReposTest(TempDirTest):
    def scan(self):
        b = self.tmp / "bin"
        b.mkdir()
        gh = b / "gh"
        gh.write_text(FAKE_GH)
        gh.chmod(gh.stat().st_mode | stat.S_IEXEC)
        out = self.tmp / "scan.txt"
        env = {**os.environ, "PATH": f"{b}:/usr/bin:/bin", "OUT": str(out), "BAD": BAD, "GOOD": GOOD}
        subprocess.run(["bash", str(SCAN), "acme", "ghost"], capture_output=True, text=True, env=env, check=True)
        return out.read_text()

    def test_flags_bad_workflows_on_any_branch_and_build_bot_commits(self):
        text = self.scan()
        self.assertIn("INFECTED  acme/hit@mega-1  build-bot commits: 0  bad workflows: megalodon.yml security audit.yml", text)
        self.assertNotIn("acme/hit@main", text)
        self.assertIn("INFECTED  acme/old@main  build-bot commits: 2", text)
        self.assertNotIn("acme/clean", text)

    def test_api_errors_are_never_counted_as_infected(self):
        text = self.scan()
        self.assertNotIn("acme/empty", text)
        self.assertIn("UNREACHABLE  acme/locked", text)
        self.assertNotIn("INFECTED  acme/locked", text)
        self.assertIn("UNREACHABLE  acme/wfdenied@main  (check failed: workflow list)", text)
        self.assertIn("UNREACHABLE  ghost  (could not list repos", text)
        self.assertIn("scan finished: 2 infected branch(es), 3 unreachable", text)
