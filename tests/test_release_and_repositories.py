# SPDX-License-Identifier: AGPL-3.0-or-later
import http.client
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import threading
import time
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from cloud_editor import CloudServer
from release_info import release_info
from repository_registry import load_repositories


class ReleaseTests(unittest.TestCase):
    def test_only_a_baked_full_commit_is_a_release(self):
        with TemporaryDirectory() as directory, patch('release_info.APP_ROOT', Path(directory)):
            path = Path(directory) / 'release.json'
            self.assertIsNone(release_info()['commit'])
            for value in ({'commit':'main'}, {'commit':'<script>'}, [], {'commit':12}):
                path.write_text(json.dumps(value), encoding='utf-8')
                self.assertIsNone(release_info()['commit'])
            commit = 'a' * 40
            path.write_text(json.dumps({'commit':commit}), encoding='utf-8')
            self.assertEqual(release_info()['url'], 'https://github.com/ontologie8/editor8/commit/' + commit)

    def test_registry_rejects_software_targets_duplicates_and_bad_roles(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'registry.json'
            for entries in ([{'repository':'ontologie8/editor8','label':'Software'}], [{'repository':'example/data','label':'A'},{'repository':'EXAMPLE/DATA','label':'B'}], [{'repository':'example/data','label':'A','users':'everyone'}], []):
                path.write_text(json.dumps(entries), encoding='utf-8')
                with self.assertRaises(ValueError):
                    load_repositories(path)


class RepositorySessionTests(unittest.TestCase):
    def setUp(self):
        self.server = CloudServer(('127.0.0.1',0), {
            'GITHUB_REPOSITORY':'example/one', 'PUBLIC_ORIGIN':'https://editor.example.org',
            'EDITOR_USERS':'tester', 'NOTARY_REVIEWERS':'tester',
            'DATA_REPOSITORIES':[{'repository':'example/one','label':'One'}, {'repository':'example/two','label':'Two','notary_reviewers':[]}],
        })
        self.server.sessions['session'] = {'token':'fake','user':'tester','csrf':'csrf','branch':'main','created':time.time()}
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.cleanup)

    def cleanup(self):
        self.server.shutdown(); self.thread.join(); self.server.server_close()

    def request(self, method, path, data=None, authenticated=True):
        headers = {'Origin':'https://editor.example.org','Content-Type':'application/json'}
        if authenticated:
            headers.update(Cookie='nac_session=session', **{'X-Editor-Token':self.server.sessions['session']['csrf']})
        connection = http.client.HTTPConnection('127.0.0.1',self.server.server_port)
        connection.request(method,path,json.dumps(data) if data is not None else None,headers)
        response = connection.getresponse()
        result = response.status, json.loads(response.read())
        connection.close()
        return result

    def test_release_is_public_but_data_targets_need_a_session(self):
        self.assertEqual(self.request('GET','/api/release', authenticated=False)[0],200)
        self.assertEqual(self.request('GET','/api/repositories', authenticated=False)[0],401)

    def test_unavailable_targets_are_hidden(self):
        def github(url, token):
            if url.endswith('/two'):
                raise HTTPError(url,404,'Unavailable',{},None)
            return {}
        with patch('cloud_editor.github_json',github):
            status, value = self.request('GET','/api/repositories')
            self.assertEqual(status,200)
            self.assertEqual([entry['repository'] for entry in value['repositories']],['example/one'])

    def test_switch_is_session_local_checks_access_and_drops_old_roles(self):
        class Store:
            def __init__(self, owner, repo, token): self.repository = owner + '/' + repo
            def slugs(self, ref): return ['demo']
            def ref(self, branch): return 'a'*40
            def case_index(self, ref): return {'repository':self.repository}
        self.server.sessions['other'] = dict(self.server.sessions['session'])
        with patch('cloud_editor.github_json',return_value={}), patch('cloud_editor.GitHubStore',Store):
            self.assertTrue(self.request('GET','/api/status')[1]['notary_reviewer'])
            self.assertEqual(self.request('GET','/api/case-index')[1]['repository'],'example/one')
            self.assertEqual(self.request('POST','/api/repositories/select',{'repository':'example/two'})[0],200)
            self.assertEqual(self.server.sessions['other'].get('repository','example/one'),'example/one')
            self.assertFalse(self.request('GET','/api/status')[1]['notary_reviewer'])
            self.assertEqual(self.request('GET','/api/case-index')[1]['repository'],'example/two')
            self.assertNotEqual(self.server.sessions['session']['csrf'],'csrf')
            self.assertEqual(self.request('POST','/api/repositories/select',{'repository':'evil/unknown'})[0],400)
            self.server.sessions['session']['branch'] = 'codex/ontology-editor-draft'
            self.assertEqual(self.request('POST','/api/repositories/select',{'repository':'example/one'})[0],400)
            self.assertEqual(self.server.sessions['session']['repository'],'example/two')

    def test_access_or_contract_failure_keeps_the_previous_target(self):
        with patch('cloud_editor.github_json',side_effect=HTTPError('https://example.org',403,'Denied',{},None)):
            self.assertEqual(self.request('POST','/api/repositories/select',{'repository':'example/two'})[0],403)
        with patch('cloud_editor.github_json',return_value={}), patch('cloud_editor.GitHubStore') as store:
            store.return_value.slugs.side_effect = ValueError('Invalid catalog')
            self.assertEqual(self.request('POST','/api/repositories/select',{'repository':'example/two'})[0],400)
        self.assertNotIn('repository',self.server.sessions['session'])
