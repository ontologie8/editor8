# SPDX-License-Identifier: AGPL-3.0-or-later
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from deploy_usage_report import definition, template, queries


class UsageReportTests(unittest.TestCase):
    def test_schedule_query_and_outbound_mail_are_separate(self):
        workflow = definition()
        recurrence = workflow["triggers"]["Weekly"]["recurrence"]
        self.assertEqual(recurrence["timeZone"], "W. Europe Standard Time")
        self.assertEqual(recurrence["schedule"], {"weekDays": ["Monday"], "hours": [8], "minutes": [0]})
        for name in ("users", "summary"):
            self.assertEqual(workflow["actions"]["Query_" + name]["inputs"]["authentication"], {"type": "ManagedServiceIdentity", "audience": "https://api.loganalytics.io"})
        self.assertFalse(template()["parameters"]["sendMail"]["defaultValue"])
        self.assertIn("sendMail", workflow["actions"]["Mail"]["expression"])

    def test_summary_counts_confirmed_identities_and_only_real_changes(self):
        self.assertIn("where isnotempty(Actor)", queries()["summary"])
        self.assertIn("summarize by Actor | count", queries()["summary"])
        self.assertIn("tobool(event.changed) == true", queries()["users"])
        self.assertIn("schema) == 1", queries()["users"])
        self.assertIn("substring(Log_s, 14)", queries()["users"])

    def test_workspace_scope_not_subscription_wide_and_existing_connection_preserved(self):
        resources = template()["resources"]
        self.assertEqual(resources[0]["condition"], "[parameters('createConnection')]")
        self.assertEqual(resources[2]["scope"], "[parameters('workspaceResourceId')]")
        self.assertNotIn("Mail.Send", str(resources))
