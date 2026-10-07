# SPDX-License-Identifier: AGPL-3.0-or-later
"""Keep the one-time GitHub App bootstrap scoped and executable on Windows."""

import os
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from register_github_app import manifest, run_az


class GitHubAppBootstrapTests(unittest.TestCase):
    def test_manifest_requests_only_editor_repository_permissions(self):
        configuration = manifest(
            "https://editor.example.org",
            "http://127.0.0.1:1234/complete",
        )
        self.assertTrue(configuration["public"])
        self.assertEqual(configuration["name"], "Ontologie8 Editor")
        self.assertEqual(configuration["default_permissions"], {
            "contents": "write",
            "pull_requests": "write",
        })
        self.assertEqual(configuration["default_events"], [])
        self.assertFalse(configuration["hook_attributes"]["active"])
        self.assertEqual(
            configuration["callback_urls"],
            ["https://editor.example.org/callback"],
        )

    def test_azure_command_uses_resolved_executable(self):
        with patch("register_github_app.shutil.which", return_value="resolved-az") as which:
            with patch(
                "register_github_app.subprocess.run",
                return_value=SimpleNamespace(returncode=0),
            ) as command:
                run_az("account", "show")
        which.assert_called_once_with("az.cmd" if os.name == "nt" else "az")
        self.assertEqual(command.call_args.args[0][0], "resolved-az")


if __name__ == "__main__":
    unittest.main()
