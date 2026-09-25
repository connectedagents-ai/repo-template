import importlib.util, unittest
from unittest import mock
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


class AppleMailScopeTest(unittest.TestCase):
    def test_only_schedule_a_accounts_reach_alerts_and_hits_and_unknown_mailboxes_are_reported(self):
        rows = [("imap://ACC1/INBOX", "alerts@godaddy.com", "Your domain will expire", 1700000000),
                ("imap://ACC2/INBOX", "alerts@godaddy.com", "Your domain will expire", 1700000000),
                ("imap://UNKNOWN/INBOX", "alerts@godaddy.com", "Your domain will expire", 1700000000)]
        hits = []
        with mock.patch.object(discover.glob, "glob", return_value=["/x/V10/MailData/Envelope Index"]), \
                mock.patch.object(discover, "mail_accounts_map",
                                  return_value={"ACC1": ("me@icloud.com", "iCloud"), "ACC2": ("other@x.com", "IMAP")}), \
                mock.patch.object(discover, "read_sqlite", return_value=rows):
            acct_rows, alerts, _, unresolved, failed = discover.apple_mail(lambda *a, **k: hits.append(a), {"me@icloud.com"})
        self.assertEqual(set(acct_rows), {"me@icloud.com"})
        self.assertEqual([a[1] for a in alerts], ["me@icloud.com"])
        self.assertEqual(len(hits), 1)
        self.assertEqual(unresolved, {"UNKNOWN"})
        self.assertFalse(failed)

    def test_an_unreadable_envelope_index_is_a_failure_not_an_empty_mailbox(self):
        with mock.patch.object(discover.glob, "glob", return_value=["/x/V10/MailData/Envelope Index"]), \
                mock.patch.object(discover, "mail_accounts_map", return_value={}), \
                mock.patch.object(discover.shutil, "copy2", side_effect=PermissionError("Operation not permitted")):
            acct_rows, alerts, _, unresolved, failed = discover.apple_mail(lambda *a, **k: None, None)
        self.assertTrue(failed)
        self.assertEqual((acct_rows, alerts, unresolved), ({}, [], set()))
