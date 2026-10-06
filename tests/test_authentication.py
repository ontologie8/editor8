# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exercise the hosted OAuth boundary without credentials or private data."""
import http.client
from io import BytesIO
import json
from pathlib import Path
import sys
import threading
import time
import unittest
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlparse
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from cloud_editor import CloudHandler, CloudServer


class AuthenticationTests(unittest.TestCase):
    def setUp(self):
        self.server = CloudServer(('127.0.0.1', 0), {
            'GITHUB_APP_CLIENT_ID': 'synthetic-client',
            'GITHUB_APP_CLIENT_SECRET': 'synthetic-secret',
            'GITHUB_REPOSITORY': 'example/data',
            'PUBLIC_ORIGIN': 'https://www.ontologie8.de',
            'EDITOR_USERS': 'tester',
        })
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.cleanup)

    def cleanup(self):
        self.server.shutdown()
        self.thread.join()
        self.server.server_close()

    def request(self, path, headers=None):
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=5)
        connection.request('GET', path, headers=headers or {})
        response = connection.getresponse()
        result = response.status, dict(response.getheaders()), response.read().decode()
        connection.close()
        return result

    def login(self):
        status, headers, _ = self.request('/login', {'Host': 'www.ontologie8.de'})
        self.assertEqual(status, 302)
        self.assertIn('HttpOnly; Secure; SameSite=Lax', headers['Set-Cookie'])
        params = parse_qs(urlparse(headers['Location']).query)
        self.assertEqual(params['redirect_uri'], ['https://www.ontologie8.de/callback'])
        self.assertEqual(params['code_challenge_method'], ['S256'])
        return params['state'][0]

    def callback(self, state):
        return self.request('/callback?state=' + state + '&code=synthetic-code', {
            'Host': 'www.ontologie8.de', 'Cookie': 'nac_oauth_state=' + state,
        })

    def test_alias_redirects_before_setting_any_oauth_cookie(self):
        status, headers, _ = self.request('/login', {'Host': 'legacy.azurecontainerapps.io'})
        self.assertEqual(status, 302)
        self.assertEqual(headers['Location'], 'https://www.ontologie8.de/login')
        self.assertNotIn('Set-Cookie', headers)
        self.assertEqual(self.server.pending, {})
        self.login()

    def test_missing_browser_cookie_does_not_contact_github(self):
        state = self.login()
        with patch('cloud_editor.urlopen') as provider:
            status, headers, body = self.request('/callback?state=' + state + '&code=synthetic-code')
        self.assertEqual(status, 401)
        provider.assert_not_called()
        self.assertIn('diesem Browser', body)
        self.assertIn('Erneut anmelden', body)
        self.assertIn('Max-Age=0', headers['Set-Cookie'])
        self.assertIn("form-action 'none'", headers['Content-Security-Policy'])
        self.assertNotIn(state, body)
        self.assertNotIn('synthetic-code', body)

    def test_expired_state_and_used_code_cannot_create_a_session(self):
        state = self.login()
        self.server.pending[state]['created'] = time.time() - 600
        with patch('cloud_editor.urlopen') as provider:
            self.assertEqual(self.callback(state)[0], 401)
        provider.assert_not_called()
        self.assertEqual(self.server.sessions, {})
        self.assertNotIn(state, self.server.pending)

    def test_provider_failures_have_safe_stage_diagnostics(self):
        cases = [
            (TimeoutError('synthetic-secret'), 503, 'github-timeout'),
            (URLError('synthetic-code'), 503, 'github-connection'),
            (PermissionError('synthetic-secret'), 503, 'github-connection'),
            (HTTPError('https://example.test/?code=synthetic-code', 502, 'synthetic-secret', {}, None), 503, 'github-http-502'),
            (HTTPError('https://example.test', 403, 'synthetic-secret', {}, None), 403, 'github-http-403'),
            (RuntimeError('synthetic-secret'), 500, 'internal-error'),
        ]
        for error, expected, category in cases:
            with self.subTest(category=category):
                state = self.login()
                with patch('cloud_editor.urlopen', side_effect=error), patch.object(CloudHandler, 'log_message') as log:
                    status, headers, body = self.callback(state)
                self.assertEqual(status, expected)
                failure = next(call for call in log.call_args_list if call.args[0].startswith('auth_failure'))
                self.assertEqual(failure.args[2], 'token-exchange')
                self.assertEqual(failure.args[3], category)
                self.assertIn(headers['X-Request-ID'], body)
                for sensitive in ('synthetic-secret', 'synthetic-code', state):
                    self.assertNotIn(sensitive, body + str(log.call_args_list))
                self.assertEqual(self.server.sessions, {})

    def test_invalid_provider_json_is_explained(self):
        state = self.login()
        with patch('cloud_editor.urlopen', return_value=BytesIO(b'not json')):
            status, _, body = self.callback(state)
        self.assertEqual(status, 502)
        self.assertIn('gültige Antwort', body)

    def test_rejected_token_has_actionable_message_without_provider_details(self):
        for error, message in [('bad_verification_code', 'bereits verwendet'), ('incorrect_client_credentials', 'Betreiber'), ('redirect_uri_mismatch', 'Callback-Adresse'), ('unknown', 'erneut beginnen')]:
            with self.subTest(error=error):
                state = self.login()
                payload = json.dumps({'error': error, 'error_description': 'synthetic-secret'}).encode()
                with patch('cloud_editor.urlopen', return_value=BytesIO(payload)):
                    status, _, body = self.callback(state)
                self.assertEqual(status, 401)
                self.assertIn(message, body)
                self.assertNotIn('synthetic-secret', body)

    def test_user_lookup_failure_is_distinguished_from_token_exchange(self):
        state = self.login()
        with patch('cloud_editor.urlopen', return_value=BytesIO(b'{"access_token":"synthetic-token"}')), patch('cloud_editor.github_json', side_effect=TimeoutError('synthetic-token')), patch.object(CloudHandler, 'log_message') as log:
            self.assertEqual(self.callback(state)[0], 503)
        failure = next(call for call in log.call_args_list if call.args[0].startswith('auth_failure'))
        self.assertEqual(failure.args[2], 'github-user')
        self.assertNotIn('synthetic-token', str(log.call_args_list))

    def test_onboarded_notary_can_login_without_granting_maintainer_or_unknown_user_access(self):
        self.server.config['EDITOR_USERS'] = 'tester,new-notary'
        self.server.repositories[0]['notary_reviewers'] = ['new-notary']
        for username in ('not-listed', 'new-notary'):
            with self.subTest(username=username):
                state = self.login()
                def provider(url, token):
                    return {'login': username} if url.endswith('/user') else {'full_name': 'example/data'}
                with patch('cloud_editor.urlopen', return_value=BytesIO(b'{"access_token":"synthetic-token"}')), patch('cloud_editor.github_json', side_effect=provider):
                    status, _, body = self.callback(state)
                if username == 'not-listed':
                    self.assertEqual(status, 401)
                    self.assertIn('nicht als Editor freigeschaltet', body)
                    self.assertEqual(self.server.sessions, {})
                else:
                    self.assertEqual(status, 302)
                    sid = next(iter(self.server.sessions))
                    status, _, body = self.request('/api/status', {'Cookie': 'nac_session=' + sid})
                    self.assertEqual(status, 200)
                    session = json.loads(body)
                    self.assertEqual(session['user'], 'new-notary')
                    self.assertTrue(session['notary_reviewer'])
                    self.assertFalse(session['ontology_maintainer'])
                    self.assertNotIn('synthetic-token', body)

    def test_repo_access_failure_and_success_follow_the_real_session_contract(self):
        for accessible in (False, True):
            with self.subTest(accessible=accessible):
                state = self.login()
                def provider(url, token):
                    self.assertEqual(token, 'synthetic-token')
                    if url.endswith('/user'):
                        return {'login': 'tester'}
                    if not accessible:
                        raise HTTPError(url, 404, 'Unavailable', {}, None)
                    return {'full_name': 'example/data'}
                with patch('cloud_editor.urlopen', return_value=BytesIO(b'{"access_token":"synthetic-token"}')) as exchange, patch('cloud_editor.github_json', side_effect=provider):
                    status, headers, body = self.callback(state)
                params = parse_qs(exchange.call_args.args[0].data.decode())
                self.assertEqual(params['redirect_uri'], ['https://www.ontologie8.de/callback'])
                self.assertIn('code_verifier', params)
                self.assertEqual(status, 302 if accessible else 401)
                if accessible:
                    self.assertEqual(headers['Location'], '/')
                    self.assertEqual(len(self.server.sessions), 1)
                    self.assertEqual(next(iter(self.server.sessions.values()))['repository'], 'example/data')
                    self.assertNotIn('synthetic-token', body + str(headers))
                    self.assertEqual(self.callback(state)[0], 401)
                else:
                    self.assertIn('Datenrepository', body)
                    self.assertEqual(self.server.sessions, {})
