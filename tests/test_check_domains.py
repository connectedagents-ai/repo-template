import os, stat, subprocess
from tests.helpers import OPS, TempDirTest

CHECK = OPS / "domains/check_domains.sh"


class CheckDomainsRedirectTest(TempDirTest):
    def web_line(self, code, location):
        b = self.tmp / "bin"
        b.mkdir(exist_ok=True)
        for name, body in (("dig", "exit 0"), ("whois", "exit 0"), ("curl", f'printf "%s" "{code} {location}"')):
            p = b / name
            p.write_text(f"#!/bin/bash\n{body}\n")
            p.chmod(p.stat().st_mode | stat.S_IEXEC)
        r = subprocess.run(["bash", str(CHECK), "old.example"], capture_output=True, text=True,
                           env={**os.environ, "PATH": f"{b}:/usr/bin:/bin"})
        return [l for l in r.stdout.splitlines() if "https://old.example " in l][0]

    def test_only_a_301_to_https_passes(self):
        self.assertIn("✅", self.web_line(301, "https://www.powerconnection.com/"))
        self.assertIn("plain http", self.web_line(301, "http://powerconnection.com/"))

    def test_308_is_permanent_and_302_is_temporary(self):
        self.assertIn("308 is permanent", self.web_line(308, "https://powerconnection.com/"))
        self.assertIn("302 is temporary", self.web_line(302, "https://powerconnection.com/"))
