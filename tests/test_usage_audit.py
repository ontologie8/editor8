# SPDX-License-Identifier: AGPL-3.0-or-later
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from usage_audit import PREFIX, audit_line, response_action


class UsageAuditTests(unittest.TestCase):
    def test_only_allowlisted_fields_leave_the_session(self):
        line = audit_line("draft_save", {"user": "synthetic-notary", "user_id": 42, "repository": "example/models", "token": "synthetic-secret", "csrf": "synthetic-code", "body": "synthetic-case-value"}, changed=True)
        event = json.loads(line[len(PREFIX):])
        self.assertEqual(event["actor"], "github:42")
        self.assertEqual(event["repository"], "example/models")
        self.assertTrue(event["changed"])
        self.assertEqual(event["schema"], 1)
        for sensitive in ("synthetic-secret", "synthetic-code", "synthetic-case-value", "csrf", "token", "body"):
            self.assertNotIn(sensitive, line)

    def test_untrusted_identity_and_repository_cannot_inject_a_log(self):
        line = audit_line("login", {"user": "name\nsecret", "user_id": True, "repository": "example/data?code=secret"})
        event = json.loads(line[len(PREFIX):])
        self.assertEqual((event["actor"], event["user"], event["repository"]), ("", "", ""))
        self.assertNotIn("secret", line)

    def test_count_completed_operations_not_previews_or_polling(self):
        for method, path, action in (("GET", "/api/cases", "repository_open"), ("GET", "/api/cases/example-a", "model_open"), ("POST", "/api/vocabulary/save", "draft_save"), ("POST", "/api/cases/example-a/review", "change_submit"), ("POST", "/api/reviews/12/review", "review_decision")):
            self.assertEqual(response_action(method, path, 200), action)
            self.assertIsNone(response_action(method, path, 400))
        for path in ("/api/status", "/api/case-index", "/api/cases/example-a/preview", "/api/cases/example-a/history", "/api/cases/example-a/turtle", "/healthz", "/callback?code=secret"):
            self.assertIsNone(response_action("GET", path, 200))
            self.assertIsNone(response_action("POST", path, 200))

    def test_denials_have_no_invented_identity(self):
        event = json.loads(audit_line("login_denied", status=401)[len(PREFIX):])
        self.assertEqual(event["actor"], "")
        self.assertEqual(response_action("POST", "/api/cases/example-a/save", 403), "access_denied")
        with self.assertRaises(ValueError):
            audit_line("arbitrary-body")

    def test_local_development_has_no_embedded_release(self):
        event = json.loads(audit_line("login", release=None)[len(PREFIX):])
        self.assertEqual(event["release"], "development")
