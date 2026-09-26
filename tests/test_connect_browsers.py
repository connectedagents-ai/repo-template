import os, stat, subprocess
from tests.helpers import OPS, TempDirTest

SCRIPT = OPS / "cowork/connect_browsers.sh"

FAKE_BROWSER = '#!/bin/bash\ntouch "$MARKS/$(basename "$0")"\necho "$@" > "$MARKS/$(basename "$0").args"\n'
FAKE_CURL = '#!/bin/bash\ncase "$*" in *9222*) [ -e "$MARKS/edge-bin" ] ;; *9223*) [ -e "$MARKS/chrome-bin" ] ;; esac\n'
FAKE_CLAUDE = '#!/bin/bash\necho "$@" >> "$MARKS/claude.log"\n[ "$2" != get ] || [ "$1" != mcp ] || exit 1\n'


class ConnectBrowsersTest(TempDirTest):
    def setUp(self):
        super().setUp()
        self.bin, self.marks = self.tmp / "bin", self.tmp / "marks"
        self.bin.mkdir()
        self.marks.mkdir()
        for name, body in [("curl", FAKE_CURL), ("claude", FAKE_CLAUDE), ("npx", "#!/bin/bash\n"),
                           ("edge-bin", FAKE_BROWSER), ("chrome-bin", FAKE_BROWSER)]:
            p = self.bin / name
            p.write_text(body)
            p.chmod(p.stat().st_mode | stat.S_IEXEC)

    def run_script(self, *args, **extra):
        env = {**os.environ, "PATH": f"{self.bin}:/usr/bin:/bin", "MARKS": str(self.marks), "WAIT_SECS": "2",
               "PROFILES": str(self.tmp / "profiles"), "EDGE_BIN": str(self.bin / "edge-bin"),
               "CHROME_BIN": str(self.bin / "chrome-bin"), **extra}
        return subprocess.run(["bash", str(SCRIPT), *args], capture_output=True, text=True, env=env)

    def test_opens_both_browsers_with_own_profiles_and_registers_them(self):
        r = self.run_script()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn('OK   edge is open and connected to Claude Code (MCP server "edge")', r.stdout)
        self.assertIn('OK   chrome is open', r.stdout)
        edge_args = (self.marks / "edge-bin.args").read_text()
        self.assertIn(f"--user-data-dir={self.tmp / 'profiles' / 'edge'}", edge_args)
        self.assertIn("--remote-debugging-port=9222", edge_args)
        log = (self.marks / "claude.log").read_text()
        self.assertIn("mcp add --scope user edge -- npx -y @playwright/mcp@latest --cdp-endpoint http://127.0.0.1:9222", log)
        self.assertIn("--cdp-endpoint http://127.0.0.1:9223", log)

    def test_missing_browser_is_reported_and_fails(self):
        r = self.run_script("edge", EDGE_BIN=str(self.tmp / "nope"))
        self.assertEqual(r.returncode, 1)
        self.assertIn("SKIP edge: not installed", r.stdout)
