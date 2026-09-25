import os, stat, subprocess
from tests.helpers import OPS, TempDirTest

INV = OPS / "cloud-inventory/inventory_cloud.sh"


class InventoryCloudTest(TempDirTest):
    def tool(self, name, body):
        b = self.tmp / "bin"
        b.mkdir(exist_ok=True)
        p = b / name
        p.write_text("#!/bin/bash\n" + body + "\n")
        p.chmod(p.stat().st_mode | stat.S_IEXEC)

    def inventory(self, **env):
        out = self.tmp / "inv.md"
        path = f"{self.tmp / 'bin'}:/usr/bin:/bin"
        r = subprocess.run(["bash", str(INV)], capture_output=True, text=True,
                           env={**os.environ, "PATH": path, "OUT": str(out), **env})
        return r, out.read_text()

    def test_1password_is_skipped_without_consent(self):
        self.tool("op", 'echo "op called" >> "$(dirname "$0")/op.log"; echo "[]"')
        r, report = self.inventory(INCLUDE_1PASSWORD="0")
        self.assertIn("consent was not given", report)
        self.assertFalse((self.tmp / "bin/op.log").exists())

    def test_a_failed_command_makes_the_run_fail_but_still_writes_the_report(self):
        self.tool("gh", "exit 1")
        r, report = self.inventory(INCLUDE_1PASSWORD="0")
        self.assertEqual(r.returncode, 1)
        self.assertIn("(failed: gh", report)
