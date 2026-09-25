import os, subprocess
from tests.helpers import OPS, TempDirTest

FOLD = OPS / "github-consolidation/merge_into_monorepo.sh"


class MergeIntoMonorepoTest(TempDirTest):
    def git(self, *args, cwd=None):
        env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
        return subprocess.run(["git", *args], cwd=cwd, env=env, check=True, capture_output=True, text=True).stdout

    def bare_repo(self, path, files, extra_branch=None):
        work = self.tmp / "w" / path
        work.mkdir(parents=True)
        self.git("init", "-q", "-b", "main", cwd=work)
        for name, body in files.items():
            (work / name).write_text(body)
        self.git("add", ".", cwd=work)
        self.git("commit", "-qm", "init", cwd=work)
        if extra_branch:
            self.git("checkout", "-qb", extra_branch, cwd=work)
            (work / "wip.txt").write_text("unmerged")
            self.git("add", ".", cwd=work)
            self.git("commit", "-qm", "wip", cwd=work)
            self.git("checkout", "-q", "main", cwd=work)
        bare = self.tmp / "base" / f"{path}.git"
        self.git("clone", "-q", "--bare", str(work), str(bare))
        return bare

    def fold(self, **env):
        return subprocess.run(["bash", str(FOLD), "--apply", "target", "src/lib", "packages/lib"], capture_output=True, text=True,
                              env={**os.environ, "GIT_BASE_URL": f"file://{self.tmp / 'base'}", "GIT_AUTHOR_NAME": "t",
                                   "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t", **env})

    def test_folds_default_branch_with_history_into_subfolder(self):
        target = self.bare_repo("connectedagents-ai/target", {"README.md": "t"})
        self.bare_repo("src/lib", {"lib.py": "x = 1"})
        r = self.fold()
        self.assertEqual(r.returncode, 0, r.stderr)
        tree = self.git("ls-tree", "-r", "--name-only", "chore/fold-in-lib", cwd=target).split()
        self.assertEqual(sorted(tree), ["README.md", "packages/lib/lib.py"])
        parents = self.git("log", "-1", "--format=%P", "chore/fold-in-lib", cwd=target).split()
        self.assertEqual(len(parents), 2)

    def test_stops_on_unmerged_source_branches_unless_acknowledged(self):
        target = self.bare_repo("connectedagents-ai/target", {"README.md": "t"})
        self.bare_repo("src/lib", {"lib.py": "x = 1"}, extra_branch="feature")
        r = self.fold()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("src/feature", r.stderr)
        self.assertNotIn("chore/fold-in-lib", self.git("branch", cwd=target))
        self.assertEqual(self.fold(FOLD_ACK_BRANCHES="1").returncode, 0)
