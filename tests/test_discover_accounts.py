import importlib.util, unittest
from tests.helpers import OPS

spec = importlib.util.spec_from_file_location("discover_accounts", OPS / "client-discovery/discover_accounts.py")
discover = importlib.util.module_from_spec(spec)
spec.loader.exec_module(discover)


class AiProjectMatchTest(unittest.TestCase):
    def test_matches_project_paths_on_the_real_host_only(self):
        self.assertTrue(discover.is_ai_project("https://claude.ai/project/123"))
        self.assertTrue(discover.is_ai_project("https://www.perplexity.ai/spaces/x?y=1"))
        self.assertFalse(discover.is_ai_project("https://example.com/share/claude.ai/project/private"))
        self.assertFalse(discover.is_ai_project("https://claude.ai.evil.com/project/1"))
        self.assertFalse(discover.is_ai_project("https://claude.ai/chat/1"))

    def test_mail_scope(self):
        self.assertTrue(discover.in_scope("Me@iCloud.com", None))
        self.assertTrue(discover.in_scope("Me@iCloud.com", {"me@icloud.com"}))
        self.assertFalse(discover.in_scope("other@x.com", {"me@icloud.com"}))
