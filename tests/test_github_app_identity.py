# SPDX-License-Identifier: AGPL-3.0-or-later
"""Reject mixed software/data ownership before registration or secret writes."""
from io import BytesIO
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from github_app_identity import existing_app
from register_github_app import register
from recover_github_app_secret import recover


class GitHubAppIdentityTests(unittest.TestCase):
    def test_bootstrap_rejects_a_data_owner_and_software_target_before_opening_browser(self):
        for owner, repository in [('notariat8', 'notariat8/ontology'),
                                  ('ontologie8', 'ontologie8/editor8'),
                                  ('ontologie8', 'https://example.test/data')]:
            with self.subTest(owner=owner, repository=repository):
                args = SimpleNamespace(origin='https://editor.example.test', app_owner=owner,
                                       data_repository=repository)
                with patch('register_github_app.HTTPServer') as server, patch('register_github_app.webbrowser.open') as browser:
                    with self.assertRaises(ValueError):
                        register(args)
                server.assert_not_called()
                browser.assert_not_called()

    def test_existing_app_is_resolved_by_verified_owner_and_client_identity(self):
        metadata = {'owner': {'login': 'ontologie8'}, 'client_id': 'synthetic-client',
                    'slug': 'synthetic-editor', 'name': 'Synthetic editor'}
        with patch('github_app_identity.urlopen', return_value=BytesIO(json.dumps(metadata).encode())) as provider:
            result = existing_app('synthetic-editor', 'synthetic-client')
        self.assertEqual(result['settings_url'], 'https://github.com/organizations/ontologie8/settings/apps/synthetic-editor')
        self.assertEqual(result['name'], 'Synthetic editor')
        self.assertNotIn('client_id', result)
        self.assertEqual(provider.call_args.args[0].full_url, 'https://api.github.com/apps/synthetic-editor')
        with patch('github_app_identity.urlopen') as provider:
            with self.assertRaises(ValueError):
                existing_app('../another-app', 'synthetic-client')
        provider.assert_not_called()

    def test_wrong_app_owner_or_client_cannot_start_secret_recovery(self):
        args = SimpleNamespace(app_owner='ontologie8', data_repository='example/models',
                               app_slug='synthetic-editor', client_id='synthetic-client')
        for owner, client in [('example', 'synthetic-client'), ('ontologie8', 'another-client')]:
            with self.subTest(owner=owner):
                metadata = {'owner': {'login': owner}, 'client_id': client,
                            'slug': 'synthetic-editor', 'name': 'Synthetic editor'}
                with patch('github_app_identity.urlopen', return_value=BytesIO(json.dumps(metadata).encode())), patch('recover_github_app_secret.HTTPServer') as server, patch('recover_github_app_secret.put_secret') as storage:
                    with self.assertRaises(ValueError):
                        recover(args)
                server.assert_not_called()
                storage.assert_not_called()
