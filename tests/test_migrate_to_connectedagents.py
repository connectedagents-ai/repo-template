import os, stat, subprocess
from tests.helpers import OPS, TempDirTest

MIGRATE = OPS / "github-consolidation/migrate_to_connectedagents.sh"

# Fake gh: repo lists come from $FAKE/<owner>.tsv (target: one name per line); transfers of names in $FAKE/fail-transfer fail.
FAKE_GH = r'''#!/bin/bash
case "$1 $2" in
  "repo list")
    f="$FAKE/$3.tsv"; [ -f "$f" ] || exit 1
    cat "$f" ;;
  "api -X")
    name="$(basename "$(dirname "$4")")"
    grep -qx "$name" "$FAKE/fail-transfer" 2>/dev/null && exit 1
    echo "$name" >> "$FAKE/transferred" ;;
  "api repos/"*) echo "connectedagents-ai/${2##*/}" ;;
  *) exit 0 ;;
esac
'''


class MigrateTest(TempDirTest):
    def setUp(self):
        super().setUp()
        self.fake = self.tmp / "fake"
        (self.tmp / "bin").mkdir()
        self.fake.mkdir()
        gh = self.tmp / "bin/gh"
        gh.write_text(FAKE_GH)
        gh.chmod(gh.stat().st_mode | stat.S_IEXEC)
        (self.fake / "connectedagents-ai.tsv").write_text("repo-template\nexisting\n")

    def owner(self, name, *repos):
        (self.fake / f"{name}.tsv").write_text("".join(f"{r}\tfalse\tfalse\tPRIVATE\n" for r in repos))

    def migrate(self, *args):
        env = {**os.environ, "PATH": f"{self.tmp / 'bin'}:{os.environ['PATH']}", "FAKE": str(self.fake)}
        return subprocess.run(["bash", str(MIGRATE), *args], cwd=self.tmp, env=env, capture_output=True, text=True)

    def plan_rows(self):
        (plan,) = self.tmp.glob("migration-plan-*.csv")
        return [ln.split(",") for ln in plan.read_text().splitlines()[1:]]

    def test_same_name_from_two_owners_moves_only_once(self):
        self.owner("OwnerA", "api", "Existing")
        self.owner("OwnerB", "API")
        r = self.migrate("OwnerA", "OwnerB")
        self.assertEqual(r.returncode, 0, r.stderr)
        actions = {(row[0], row[1]): row[3] for row in self.plan_rows()}
        self.assertEqual(actions, {("OwnerA", "api"): "transfer", ("OwnerA", "Existing"): "collision-needs-merge",
                                   ("OwnerB", "API"): "collision-needs-merge"})

    def test_failed_transfer_and_unlistable_owner_exit_nonzero(self):
        self.owner("OwnerA", "ok", "bad")
        (self.fake / "fail-transfer").write_text("bad\n")
        r = self.migrate("--apply", "OwnerA", "Missing")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("OwnerA/bad (failed)", r.stderr)
        self.assertIn("Missing (listing failed)", r.stderr)
        self.assertEqual((self.fake / "transferred").read_text().split(), ["ok"])

    def test_aborts_when_target_cannot_be_listed(self):
        (self.fake / "connectedagents-ai.tsv").unlink()
        self.owner("OwnerA", "api")
        r = self.migrate("OwnerA")
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(list(self.tmp.glob("migration-plan-*.csv")), [])
