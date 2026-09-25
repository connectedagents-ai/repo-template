import importlib.util, subprocess
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

    def test_path_variables_are_not_keys_but_pat_is(self):
        rc = self.tmp / ".zshrc"
        rc.write_text('export PATH="/opt/homebrew/bin:/usr/bin"\nexport PYTHONPATH=/Users/me/code/lib\n'
                      'export GITHUB_PAT=fake-github-value-5\n')
        r = self.run_py(FIND, "--no-defaults", rc)
        self.assertIn("GITHUB_PAT", r.stdout)
        self.assertNotIn("PATH ", r.stdout.replace("GITHUB_PAT", ""))
        self.assertEqual(r.stdout.count("\n- "), 1)

    def test_npmrc_registry_tokens_are_found(self):
        rc = self.tmp / ".npmrc"
        rc.write_text("//registry.npmjs.org/:_authToken=fake-npm-value-6\n//npm.pkg.github.com/:_authToken=${GH_PKG}\n")
        r = self.run_py(FIND, "--no-defaults", rc)
        self.assertIn("//registry.npmjs.org/:_authToken", r.stdout)
        self.assertIn("npmjs.com/settings", r.stdout)
        self.assertNotIn("npm.pkg.github.com", r.stdout)

    def test_rotate_links_go_to_the_right_provider(self):
        spec = importlib.util.spec_from_file_location("fpk", FIND)
        fpk = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fpk)
        self.assertIn("twilio", fpk.rotate_url("TWILIO_AUTH_TOKEN"))
        self.assertIn("supabase", fpk.rotate_url("SUPABASE_DB_PASSWORD"))
        self.assertIn("npmjs", fpk.rotate_url("//registry.npmjs.org/:_authToken"))
        self.assertIn("npmjs", fpk.rotate_url("NPM_TOKEN"))
        self.assertIn("github", fpk.rotate_url("//npm.pkg.github.com/:_authToken"))

    def test_key_in_git_history_is_flagged_but_merely_staged_is_not(self):
        repo = self.tmp / "repo"
        repo.mkdir()
        git = ["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t"]
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        (repo / ".env").write_text("XAI_API_KEY=fake-xai-value-4\n")
        subprocess.run(git + ["add", ".env"], check=True)
        r = self.run_py(FIND, "--no-defaults", repo, check=False)
        self.assertEqual(r.returncode, 0)
        self.assertIn("tracked by git", r.stdout)
        subprocess.run(git + ["commit", "-qm", "oops"], check=True)
        r = self.run_py(FIND, "--no-defaults", repo, check=False)
        self.assertEqual(r.returncode, 1)
        self.assertIn("IN GIT HISTORY", r.stdout)

    def test_quoted_values_with_spaces_are_scanned_whole(self):
        rc = self.tmp / ".zshrc"
        rc.write_text('export DB_PASSWORD="correct horse battery staple"\n')
        self.assertIn("DB_PASSWORD", self.run_py(FIND, "--no-defaults", rc).stdout)

    def test_unreadable_files_make_the_scan_incomplete(self):
        d = self.tmp / "cfg"
        d.mkdir()
        (d / "settings.json").symlink_to(d / "missing.json")
        r = self.run_py(FIND, "--no-defaults", d, check=False)
        self.assertEqual(r.returncode, 2)
        self.assertIn("INCOMPLETE", r.stdout)

    def test_escaped_quotes_stay_inside_the_value(self):
        rc = self.tmp / ".zshrc"
        rc.write_text('export DB_PASSWORD="ab\\"cdefghijk"\n')
        self.assertIn("DB_PASSWORD", self.run_py(FIND, "--no-defaults", rc).stdout)

    def test_key_first_added_by_a_merge_resolution_is_in_git_history(self):
        repo = self.tmp / "repo"
        repo.mkdir()
        git = ["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t"]
        subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
        env = repo / ".env"
        env.write_text("MODE=base\n")
        subprocess.run(git + ["add", ".env"], check=True)
        subprocess.run(git + ["commit", "-qm", "base"], check=True)
        subprocess.run(git + ["checkout", "-qb", "side"], check=True)
        env.write_text("MODE=side\n")
        subprocess.run(git + ["commit", "-qam", "side"], check=True)
        subprocess.run(git + ["checkout", "-q", "main"], check=True)
        env.write_text("MODE=main\n")
        subprocess.run(git + ["commit", "-qam", "main"], check=True)
        subprocess.run(git + ["merge", "-q", "side"], capture_output=True)
        env.write_text("MODE=merged\nXAI_API_KEY=fake-xai-merge-value-7\n")
        subprocess.run(git + ["commit", "-qam", "merge"], check=True)
        r = self.run_py(FIND, "--no-defaults", repo, check=False)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("IN GIT HISTORY", r.stdout)
