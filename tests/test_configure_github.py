import os, stat, subprocess
from tests.helpers import OPS, TempDirTest

SCRIPT = OPS / "github-setup/configure_github.sh"

FAKE_GH = r'''#!/bin/bash
body=""; case " $* " in *" --input - "*) body="$(cat)";; esac
printf '%s\t%s\n' "$*" "$(printf '%s' "$body" | tr -d '\n')" >> "$GH_LOG"
case "$*" in
  *"$FAIL_ON"*) [ -n "$FAIL_ON" ] && { echo "HTTP 403: Upgrade to GitHub Team" >&2; exit 1; } ;;
esac
case "$*" in
  "api user --jq .login") echo me ;;
  "api orgs/acme/memberships/me --jq .role") echo "$ROLE" ;;
  "api orgs/acme --jq .plan.name") echo free ;;
  "api orgs/acme/teams/maintainers") exit 1 ;;
  "api orgs/acme/code-security/configurations --jq"*) ;;
  "api orgs/acme/rulesets --jq"*) ;;
  "api orgs/acme/copilot/billing"*) exit 1 ;;
  "repo list"*) printf 'alpha\nbeta\n' ;;
  "api -X POST orgs/acme/code-security/configurations --input -") echo "warning: slow network" >&2; echo "${CONFIG_RESP:-{\"id\": 42\}}" ;;
  "api -X"*) echo '{}' ;;
  *) exit 1 ;;
esac
'''


class ConfigureGithubTest(TempDirTest):
    def run_script(self, *args, role="admin", fail_on="", config_resp=None):
        b = self.tmp / "bin"
        b.mkdir(exist_ok=True)
        gh = b / "gh"
        gh.write_text(FAKE_GH)
        gh.chmod(gh.stat().st_mode | stat.S_IEXEC)
        self.gh_log = self.tmp / "gh.log"
        env = {**os.environ, "PATH": f"{b}:/usr/bin:/bin", "GH_LOG": str(self.gh_log), "ROLE": role, "FAIL_ON": fail_on}
        if config_resp is not None:
            env["CONFIG_RESP"] = config_resp
        r = subprocess.run(["bash", str(SCRIPT), *args, "acme"], capture_output=True, text=True, env=env, cwd=self.tmp)
        return r, self.gh_log.read_text() if self.gh_log.exists() else ""

    def test_dry_run_changes_nothing(self):
        r, calls = self.run_script()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("api -X", calls)
        self.assertIn("WOULD PATCH orgs/acme", r.stderr)
        self.assertIn("WOULD POST orgs/acme/rulesets", r.stderr)
        self.assertIn("WOULD PATCH repos/acme/beta", r.stderr)

    def test_apply_sets_org_ruleset_security_and_every_repo(self):
        r, calls = self.run_script("--apply")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('api -X POST orgs/acme/rulesets --input -\t{  "name": "protect-main"', calls)
        self.assertIn("api -X POST orgs/acme/code-security/configurations/42/attach", calls)
        self.assertIn("api -X PUT orgs/acme/code-security/configurations/42/defaults", calls)
        for repo in ("alpha", "beta"):
            self.assertIn(f"api -X PATCH repos/acme/{repo} --input -", calls)
            self.assertIn(f"api -X PUT repos/acme/{repo}/automated-security-fixes", calls)
        self.assertNotIn("orgs/acme/repos", calls)

    def test_create_repos_adds_the_blueprint_repos(self):
        r, calls = self.run_script("--apply", "--create-repos")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('"name": ".github", "private": false', calls)
        self.assertIn('"name": "litigationforce", "private": true', calls)
        self.assertIn('api -X PATCH repos/acme/config --input -\t{"is_template": true}', calls)

    def test_a_failed_change_is_reported_and_the_run_continues(self):
        r, calls = self.run_script("--apply", fail_on="orgs/acme/rulesets --input")
        self.assertEqual(r.returncode, 1)
        self.assertIn("FAIL  POST orgs/acme/rulesets", r.stderr)
        self.assertIn("api -X PATCH repos/acme/beta", calls)

    def test_refuses_without_owner_role(self):
        r, calls = self.run_script("--apply", role="member")
        self.assertEqual(r.returncode, 1)
        self.assertIn("not an owner", r.stderr)
        self.assertNotIn("api -X", calls)

    def test_an_unreadable_configuration_id_is_a_failure_not_a_silent_skip(self):
        r, calls = self.run_script("--apply", config_resp="not json")
        self.assertEqual(r.returncode, 1)
        self.assertIn("NOT attached", r.stderr)
        self.assertNotIn("/attach", calls)
