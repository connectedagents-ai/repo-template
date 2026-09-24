import json
from tests.helpers import OPS, TempDirTest

PARK = OPS / "mcp/park_mcp_servers.py"


class ParkMcpTest(TempDirTest):
    def test_json_config_keeps_core_and_parks_the_rest_reversibly(self):
        cfg = self.tmp / "mcp.json"
        original = {"mcpServers": {"github": {"command": "gh"}, "shell": {"command": "sh"}}, "theme": "dark"}
        cfg.write_text(json.dumps(original))
        self.run_py(PARK, "--config", cfg, "--keep", "github", "--apply")
        self.assertEqual(json.loads(cfg.read_text()), {"mcpServers": {"github": {"command": "gh"}}, "theme": "dark"})
        self.assertEqual(json.loads((self.tmp / "mcp.parked.json").read_text())["mcpServers"], {"shell": {"command": "sh"}})
        (backup,) = self.tmp.glob("mcp.json.bak-*")
        self.assertEqual(json.loads(backup.read_text()), original)

    def test_codex_toml_parks_whole_server_tables(self):
        cfg = self.tmp / "config.toml"
        cfg.write_text('model = "x"\n\n[mcp_servers.github]\ncommand = "gh"\n\n'
                       '[mcp_servers.shell]\ncommand = "sh"\n[mcp_servers.shell.env]\nA = "1"\n')
        self.run_py(PARK, "--config", cfg, "--keep", "github", "--apply")
        kept, parked = cfg.read_text(), (self.tmp / "mcp.parked.toml").read_text()
        self.assertIn('model = "x"', kept)
        self.assertIn("[mcp_servers.github]", kept)
        self.assertNotIn("shell", kept)
        self.assertIn("[mcp_servers.shell.env]", parked)

    def test_dry_run_changes_nothing_and_flags_inline_secrets(self):
        cfg = self.tmp / "mcp.json"
        body = json.dumps({"mcpServers": {"github": {"env": {"GITHUB_TOKEN": "ghp_x"}}, "shell": {}}})
        cfg.write_text(body)
        r = self.run_py(PARK, "--config", cfg, "--keep", "github")
        self.assertIn("inline secret GITHUB_TOKEN", r.stdout)
        self.assertEqual(cfg.read_text(), body)
        self.assertEqual(list(self.tmp.glob("mcp.parked.*")), [])

    def test_refuses_to_park_everything(self):
        cfg = self.tmp / "mcp.json"
        cfg.write_text("{}")
        self.assertNotEqual(self.run_py(PARK, "--config", cfg, check=False).returncode, 0)
