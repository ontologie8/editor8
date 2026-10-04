# SPDX-License-Identifier: AGPL-3.0-or-later
import base64
from contextlib import contextmanager
import http.client
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from rdflib import Graph, Literal
from fixtures import DemoDataset
from case_document import render
from case_editor_model import N8
from data_contract import APP_ROOT, local_root, parse_baseline
from case_editor_model import load_case, prepare_change
from case_index import build_case_index
from github_store import GitHubStore
from cloud_editor import CloudServer

class ContractTests(unittest.TestCase):
    def setUp(self):
        self.demo=DemoDataset()
        self.addCleanup(self.demo.close)
    def test_bad_version_duplicates_and_path_escape_fail_before_case_reads(self):
        for ids in [['demo','demo'],['../outside'],['A/secret'],[],[None]]:
            with self.subTest(ids=ids), self.assertRaises(ValueError):
                parse_baseline(json.dumps({'business_case_type_ids':ids}))
        with self.assertRaises(ValueError):
            parse_baseline(json.dumps({'editor_contract_version':2,'business_case_type_ids':['demo']}))
        with self.assertRaises(ValueError): local_root(APP_ROOT)
        with self.assertRaises(ValueError): GitHubStore('ontologie8','editor8','fake')
    def test_missing_local_configuration_never_uses_software_as_data(self):
        env=dict(os.environ); env.pop('EDITOR8_DATA_ROOT',None); env['PYTHONDONTWRITEBYTECODE']='1'
        result=subprocess.run([sys.executable,'-c', 'import sys; sys.path.insert(0,"scripts"); from case_editor_model import slugs; slugs()'],cwd=APP_ROOT,env=env,capture_output=True,text=True)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('EDITOR8_DATA_ROOT',result.stderr)
    def test_remote_snapshot_needs_no_local_models_and_pins_baseline_and_files(self):
        store=GitHubStore('example','dataset','fake')
        sha='a'*40; seen=[]
        def read(path,ref):
            seen.append((path,ref))
            return (self.demo.root/path).read_text(encoding='utf-8')
        with patch.object(store,'read_file',side_effect=read), patch.object(store,'ref',return_value=sha):
            case=store.load_case('demo-eins','main')
            self.assertEqual(case['expected_ref'],sha)
            self.assertEqual(len(case['nodes']),5)
            index=store.case_index()
            self.assertEqual(index['case_count'],2)
            self.assertEqual(len(index['entries']),10)
            with self.assertRaisesRegex(ValueError,'Unbekannter Fall'):
                store.load_case('../private','main')
        self.assertEqual({ref for _,ref in seen},{sha})
        self.assertEqual(sum(path=='catalog/nac-baseline.json' for path,_ in seen),1)
        self.assertFalse(any('private' in path for path,_ in seen))
    def test_edit_roundtrip_and_conflicts_with_synthetic_models(self):
        model=load_case('demo-eins',self.demo.root)
        ttl,page,changed=prepare_change('demo-eins',model,model['revision'],self.demo.root)
        self.assertFalse(changed)
        model['summary']='Geändertes künstliches Beispiel'
        ttl,page,changed=prepare_change('demo-eins',model,model['revision'],self.demo.root)
        self.assertTrue(changed)
        self.assertIn('flowchart LR',page)
        self.assertIn('github.com/ontologie8/editor8',page)
        store=GitHubStore('example','dataset','fake')
        with patch.object(store,'ref',return_value='b'*40), patch.object(store,'request') as request:
            with self.assertRaisesRegex(ValueError,'inzwischen'):
                store.save('demo-eins','codex/ontology-editor-test',{**model,'expected_ref':'a'*40})
            request.assert_not_called()
    def test_detailed_document_version_preserves_local_source_notes(self):
        baseline=self.demo.root/'catalog/nac-baseline.json'
        data=json.loads(baseline.read_text(encoding='utf-8'))
        graph=Graph().parse(self.demo.root/'cases/demo-eins/ontology.ttl',format='turtle')
        node=N8['case/demo-eins/node/demo0']
        graph.remove((node,N8.nacNodeId,None))
        graph.add((node,N8.lokaleNodeId,Literal('demo0')))
        graph.add((node,N8.quellabschnitt,Literal('II')))
        self.assertNotIn('Ergänzungen aus der Fachvorlage',render('demo-eins',graph,root=self.demo.root))
        data['editor_document_version']=2
        baseline.write_text(json.dumps(data),encoding='utf-8')
        detailed=render('demo-eins',graph,root=self.demo.root)
        self.assertIn('Ergänzungen aus der Fachvorlage',detailed)
        self.assertIn('| II | Beispiel Angabenfrage |',detailed)
        for bad in [True,3,'2']:
            with self.subTest(version=bad), self.assertRaises(ValueError):
                parse_baseline(json.dumps({**data,'editor_document_version':bad}))

    def test_index_requires_full_catalog_even_for_two_cases(self):
        read=lambda path:(self.demo.root/path).read_text(encoding='utf-8')
        with self.assertRaises(ValueError):
            build_case_index(read('catalog/nac-usecases.ttl'),{'demo-eins':read('cases/demo-eins/ontology.ttl')},'a'*40)
    def test_cloud_assets_health_and_auth_work_without_a_local_dataset(self):
        server=CloudServer(('127.0.0.1',0),{'GITHUB_REPOSITORY':'example/dataset','PUBLIC_ORIGIN':'https://example.org','EDITOR_USERS':'tester','GITHUB_APP_CLIENT_ID':'fake','GITHUB_APP_CLIENT_SECRET':'fake'})
        thread=threading.Thread(target=server.serve_forever,daemon=True); thread.start()
        try:
            for path,expected in [('/healthz',200),('/',200),('/app.js',200),('/interaction.js',200),('/learning/?mode=handbook',200),('/learning/content.js',200),('/learning/app.js',200),('/learning/style.css',200),('/learning/../../.git/config',404),('/learning/course.json',404),('/assets/brand/e8_32.png',200),('/assets/brand/n8_192.png',200),('/assets/brand/e8_526.png',200),('/assets/brand/../../.git/config',404),('/assets/brand/unknown.png',404),('/api/status',401),('/catalog/nac-baseline.json',404),('/.git/config',404)]:
                with self.subTest(path=path):
                    conn=http.client.HTTPConnection('127.0.0.1',server.server_port); conn.request('GET',path)
                    response=conn.getresponse(); self.assertEqual(response.status,expected)
                    if path.startswith('/learning/') and expected == 200:
                        self.assertIn("frame-ancestors 'self'", response.getheader('Content-Security-Policy'))
                    elif path == '/':
                        self.assertIn("frame-ancestors 'none'", response.getheader('Content-Security-Policy'))
                    response.read(); conn.close()
        finally: server.shutdown(); thread.join(); server.server_close()
