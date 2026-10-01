# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check hosted editor session and origin gates without external services."""

import http.client
from io import BytesIO
import json
import os
from pathlib import Path
import sys
import threading
import time
import unittest
from urllib.parse import parse_qs, urlparse
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from case_editor_model import ROOT

from cloud_editor import CloudHandler, CloudServer, require_config
from case_editor_model import load_case
from vocabulary_editor import model as vocabulary_model


class CloudEditorTests(unittest.TestCase):
    def test_case_draft_can_be_put_aside_and_cannot_change_another_case(self):
        branch = "codex/ontology-editor-reviewer-20260929100000-a1b2c3"
        self.server.sessions["switch-session"] = {
            "token": "fake", "user": "reviewer", "csrf": "switch-csrf", "branch": branch,
            "purpose": "case", "case": "erbausschlagung", "created": time.time(),
        }
        cookie = {"Cookie": "nac_session=switch-session"}
        headers = {**cookie, "Origin": "https://editor.example.org", "X-Editor-Token": "switch-csrf", "Content-Type": "application/json"}
        reads = []

        class FakeStore:
            def slugs(self, ref):
                from case_editor_model import slugs
                return slugs()

            def __init__(self, *_):
                pass

            def load_case(self, slug, ref):
                reads.append((slug, ref))
                return {"title": slug, "expected_ref": "a" * 40}

            def list_drafts(self, user):
                assert user == "reviewer"
                return [{"branch": branch, "purpose": "case", "case": ""}]

        with patch("cloud_editor.GitHubStore", FakeStore):
            status, _, body = self.request("GET", "/api/cases/immobilienkaufvertrag", headers=cookie)
            self.assertEqual(status, 200)
            self.assertEqual(reads[-1], ("immobilienkaufvertrag", "main"))
            self.assertEqual(self.request("POST", "/api/cases/immobilienkaufvertrag/save", body="{}", headers=headers)[0], 400)
            self.assertEqual(self.request("POST", "/api/start-branch", body='{"purpose":"case","case":"immobilienkaufvertrag"}', headers=headers)[0], 400)
            self.assertEqual(self.request("POST", "/api/drafts/leave", body="{}", headers=headers)[0], 200)
            self.assertEqual(self.server.sessions["switch-session"]["branch"], "main")
            self.assertEqual(self.server.sessions["switch-session"]["case"], "")
            status, _, body = self.request("POST", "/api/drafts/resume", body=json.dumps({"branch": branch, "case": "immobilienkaufvertrag"}), headers=headers)
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(body)["case"], "immobilienkaufvertrag")
            self.assertEqual(reads[-1], ("immobilienkaufvertrag", branch))
            self.assertEqual(self.server.sessions["switch-session"]["case"], "immobilienkaufvertrag")

    def test_saved_draft_can_only_be_resumed_by_its_owner(self):
        branch = "codex/ontology-editor-reviewer-20260929100000-a1b2c3"
        self.server.sessions["draft-session"] = {
            "token": "fake", "user": "reviewer", "csrf": "draft-csrf", "branch": "main", "created": time.time(),
        }
        cookie = {"Cookie": "nac_session=draft-session"}
        headers = {**cookie, "Origin": "https://editor.example.org", "X-Editor-Token": "draft-csrf", "Content-Type": "application/json"}

        class FakeStore:
            def slugs(self, ref):
                from case_editor_model import slugs
                return slugs()

            def __init__(self, *_):
                pass

            def list_drafts(self, user):
                assert user == "reviewer"
                return [{"branch": branch, "purpose": "case", "case": "erbausschlagung"}]

            def load_case(self, slug, ref):
                assert (slug, ref) == ("erbausschlagung", branch)
                return {"title": "Erbausschlagung"}

        with patch("cloud_editor.GitHubStore", FakeStore):
            status, _, body = self.request("GET", "/api/drafts", headers=cookie)
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(body)[0]["branch"], branch)
            status, _, _ = self.request("POST", "/api/drafts/resume", body=json.dumps({"branch": "codex/ontology-editor-other-20260929120000-a1b2c3"}), headers=headers)
            self.assertEqual(status, 400)
            self.assertEqual(self.server.sessions["draft-session"]["branch"], "main")
            status, _, body = self.request("POST", "/api/drafts/resume", body=json.dumps({"branch": branch}), headers=headers)
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(body)["case"], "erbausschlagung")
            self.assertEqual(self.server.sessions["draft-session"]["branch"], branch)
            self.assertEqual(self.request("POST", "/api/drafts/resume", body=json.dumps({"branch": branch}), headers=headers)[0], 400)

    def test_vocabulary_draft_needs_current_maintainer_role(self):
        branch = "codex/ontology-vocabulary-reviewer-20260929110000-d4e5f6"
        self.server.sessions["vocab-draft"] = {
            "token": "fake", "user": "reviewer", "csrf": "draft-csrf", "branch": "main", "created": time.time(),
        }
        cookie = {"Cookie": "nac_session=vocab-draft"}
        headers = {**cookie, "Origin": "https://editor.example.org", "X-Editor-Token": "draft-csrf", "Content-Type": "application/json"}

        class FakeStore:
            def slugs(self, ref):
                from case_editor_model import slugs
                return slugs()

            def __init__(self, *_):
                pass

            def list_drafts(self, user):
                return [{"branch": branch, "purpose": "vocabulary", "case": ""}]

            def load_vocabulary(self, ref):
                assert ref == branch
                return {"terms": []}

        with patch("cloud_editor.GitHubStore", FakeStore):
            self.assertEqual(json.loads(self.request("GET", "/api/drafts", headers=cookie)[2]), [])
            self.assertEqual(self.request("POST", "/api/drafts/resume", body=json.dumps({"branch": branch}), headers=headers)[0], 403)
            self.server.config["ONTOLOGY_MAINTAINERS"] = "reviewer"
            self.assertEqual(json.loads(self.request("GET", "/api/drafts", headers=cookie)[2])[0]["branch"], branch)
            self.assertEqual(self.request("POST", "/api/drafts/resume", body=json.dumps({"branch": branch}), headers=headers)[0], 200)
            self.assertEqual(self.server.sessions["vocab-draft"]["purpose"], "vocabulary")

    def test_historical_case_becomes_a_separate_review_branch(self):
        main, target = "a" * 40, "b" * 40
        self.server.sessions["restore-session"] = {
            "token": "fake", "user": "reviewer", "csrf": "restore-csrf", "branch": "main", "created": time.time(),
        }
        cookie = {"Cookie": "nac_session=restore-session"}
        headers = {**cookie, "Origin": "https://editor.example.org", "X-Editor-Token": "restore-csrf", "Content-Type": "application/json"}

        class FakeStore:
            def slugs(self, ref):
                from case_editor_model import slugs
                return slugs()

            def __init__(self, *_):
                pass

            def case_history(self, slug):
                return {"main_ref": main, "case": slug, "entries": [{"sha": target, "message": "Frühere Fassung"}]}

            def preview_case_restore(self, slug, target_sha, expected_main):
                assert (slug, target_sha, expected_main) == ("erbausschlagung", target, main)
                return {"changed": True, "changes": ["Fachfrage geändert"], "main_ref": main, "target_sha": target}

            def restore_case(self, slug, target_sha, expected_main, branch):
                assert (slug, target_sha, expected_main) == ("erbausschlagung", target, main)
                return {"branch": branch, "expected_ref": "c" * 40, "changes": ["Fachfrage geändert"]}

        payload = json.dumps({"target_sha": target, "expected_main": main})
        with patch("cloud_editor.GitHubStore", FakeStore):
            status, _, body = self.request("GET", "/api/cases/erbausschlagung/history", headers=cookie)
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(body)["entries"][0]["sha"], target)
            status, _, body = self.request("POST", "/api/cases/erbausschlagung/restore-preview", body=payload, headers=headers)
            self.assertEqual(status, 200)
            self.assertTrue(json.loads(body)["changed"])
            status, _, body = self.request("POST", "/api/cases/erbausschlagung/restore", body=payload, headers=headers)
            self.assertEqual(status, 200)
            self.assertTrue(json.loads(body)["branch"].startswith("codex/ontology-editor-reviewer-"))
            self.assertEqual(self.server.sessions["restore-session"]["branch"], json.loads(body)["branch"])
            self.assertEqual(self.request("POST", "/api/cases/erbausschlagung/restore", body=payload, headers=headers)[0], 400)

    def test_vocabulary_has_separate_branch_and_maintainer_gate(self):
        self.server.config["ONTOLOGY_MAINTAINERS"] = "maintainer"
        self.server.sessions["vocabulary-session"] = {
            "token": "fake", "user": "maintainer", "csrf": "csrf-vocab", "branch": "main", "created": time.time(),
        }
        cookie = {"Cookie": "nac_session=vocabulary-session"}
        headers = {**cookie, "Origin": "https://editor.example.org", "X-Editor-Token": "csrf-vocab", "Content-Type": "application/json"}
        source = (ROOT / "ontology/core.ttl").read_text(encoding="utf-8")
        impact_calls = []
        case_index_calls = []
        catalog_reads = []
        main_sha = ["a" * 40]

        class FakeStore:
            def slugs(self, ref):
                from case_editor_model import slugs
                return slugs()

            def __init__(self, *_):
                pass

            def create_branch(self, branch):
                return "main-ref"

            def ref(self, branch):
                return main_sha[0]

            def load_vocabulary(self, branch):
                result = vocabulary_model(source)
                result["expected_ref"] = "main-ref"
                return result

            def vocabulary_impact(self, main_ref):
                impact_calls.append(main_ref)
                return {"source_ref": main_ref, "case_count": 20, "terms": {"Angabenfrage": [{"slug": "immobilienkaufvertrag", "count": 9}]}}

            def case_index(self, main_ref):
                case_index_calls.append(main_ref)
                return {"source_ref": main_ref, "case_count": 20, "entries": [{"slug": "immobilienkaufvertrag", "node_id": "one", "label": "Eintrag"}]}

            def read_file(self, path, ref):
                catalog_reads.append((path, ref))
                return (ROOT / path).read_text(encoding="utf-8")

            def preview_vocabulary(self, branch, data):
                return {"changed": True, "changes": ["Bezeichnung geändert"]}

            def save_vocabulary(self, branch, data):
                return {"changed": True, "revision": data["revision"], "expected_ref": "new-ref"}

            def create_vocabulary_pr(self, branch, reason, source):
                return "https://github.com/notariat8/ontology/pull/18"

            def load_case(self, slug, branch):
                result = load_case(slug)
                result["expected_ref"] = "main-ref"
                return result

        with patch("cloud_editor.GitHubStore", FakeStore):
            status, _, body = self.request("GET", "/api/status", headers=cookie)
            self.assertEqual(status, 200)
            self.assertTrue(json.loads(body)["ontology_maintainer"])
            status, _, body = self.request("POST", "/api/start-branch", body='{"purpose":"vocabulary"}', headers=headers)
            self.assertEqual(status, 200)
            self.assertIn("ontology-vocabulary-", json.loads(body)["branch"])
            status, _, body = self.request("GET", "/api/vocabulary", headers=cookie)
            self.assertEqual(status, 200)
            proposed = json.loads(body)
            self.assertEqual(len(proposed["terms"]), len(vocabulary_model(source)["terms"]))
            status, _, body = self.request("GET", "/api/vocabulary/impact", headers=cookie)
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(body)["terms"]["Angabenfrage"][0]["count"], 9)
            self.assertEqual(self.request("GET", "/api/vocabulary/impact", headers=cookie)[0], 200)
            self.assertEqual(impact_calls, ["a" * 40])
            main_sha[0] = "b" * 40
            status, _, body = self.request("GET", "/api/vocabulary/impact", headers=cookie)
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(body)["source_ref"], "b" * 40)
            self.assertEqual(impact_calls, ["a" * 40, "b" * 40])
            status, _, body = self.request("GET", "/api/case-index", headers=cookie)
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(body)["source_ref"], "b" * 40)
            self.assertEqual(self.request("GET", "/api/case-index", headers=cookie)[0], 200)
            self.assertEqual(case_index_calls, ["b" * 40])
            status, _, body = self.request("GET", "/api/cases", headers=cookie)
            self.assertEqual(status, 200)
            self.assertEqual(len(json.loads(body)), 20)
            self.assertEqual(catalog_reads, [("catalog/nac-usecases.ttl", "b" * 40)])
            status, _, _ = self.request("POST", "/api/cases/immobilienkaufvertrag/save", body=json.dumps(load_case("immobilienkaufvertrag")), headers=headers)
            self.assertEqual(status, 400)
            status, _, _ = self.request("POST", "/api/vocabulary/preview", body=json.dumps(proposed), headers=headers)
            self.assertEqual(status, 200)
            status, _, _ = self.request("POST", "/api/vocabulary/save", body=json.dumps(proposed), headers=headers)
            self.assertEqual(status, 200)
            status, _, body = self.request("POST", "/api/vocabulary/review", body=json.dumps({"reason": "Fachliche Änderung der Begriffe", "source": "NaC-Commit abc123"}), headers=headers)
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(body)["branch"], "main")
        self.server.sessions["vocabulary-session"]["user"] = "other"
        status, _, _ = self.request("POST", "/api/start-branch", body='{"purpose":"vocabulary"}', headers=headers)
        self.assertEqual(status, 403)

    def test_oauth_code_is_not_written_to_request_log(self):
        handler = Mock()
        handler.command = "GET"
        handler.path = "/callback?code=one-time-secret&state=state-value"
        CloudHandler.log_request(handler, 302)
        self.assertNotIn("one-time-secret", str(handler.log_message.call_args))
        self.assertIn("/callback", str(handler.log_message.call_args))

    def test_notary_reviewer_must_be_a_configured_editor(self):
        config = {
            "GITHUB_APP_CLIENT_ID": "example", "GITHUB_APP_CLIENT_SECRET": "example-secret",
            "GITHUB_REPOSITORY": "notariat8/ontology", "PUBLIC_ORIGIN": "https://editor.example.org",
            "EDITOR_USERS": "reviewer", "NOTARY_REVIEWERS": "someone-else",
        }
        with patch.dict(os.environ, config, clear=True):
            with self.assertRaisesRegex(ValueError, "Teilmenge"):
                require_config()
            os.environ["NOTARY_REVIEWERS"] = "reviewer"
            self.assertEqual(require_config()["NOTARY_REVIEWERS"], "reviewer")
            os.environ["ONTOLOGY_MAINTAINERS"] = "someone-else"
            with self.assertRaisesRegex(ValueError, "ONTOLOGY_MAINTAINERS"):
                require_config()
            os.environ["ONTOLOGY_MAINTAINERS"] = "reviewer"
            self.assertEqual(require_config()["ONTOLOGY_MAINTAINERS"], "reviewer")

    def setUp(self):
        self.server = CloudServer(("127.0.0.1", 0), {
            "GITHUB_APP_CLIENT_ID": "example",
            "GITHUB_APP_CLIENT_SECRET": "not-a-real-secret",
            "GITHUB_REPOSITORY": "notariat8/ontology",
            "PUBLIC_ORIGIN": "https://editor.example.org",
            "EDITOR_USERS": "reviewer",
        })
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)

    def request(self, method, path, body=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        connection.request(method, path, body=body, headers=headers or {})
        response = connection.getresponse()
        result = response.status, dict(response.getheaders()), response.read()
        connection.close()
        return result

    def test_session_required_and_csrf_blocks_cross_origin_write(self):
        status, _, body = self.request("GET", "/healthz")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body), {"status": "ok"})
        status, _, _ = self.request("GET", "/api/status")
        self.assertEqual(status, 401)
        status, _, _ = self.request("GET", "/api/cases/immobilienkaufvertrag/turtle")
        self.assertEqual(status, 401)
        status, _, _ = self.request("GET", "/api/case-index")
        self.assertEqual(status, 401)
        status, _, _ = self.request("GET", "/api/cases/erbausschlagung/history")
        self.assertEqual(status, 401)
        status, _, _ = self.request("GET", "/api/drafts")
        self.assertEqual(status, 401)
        status, _, _ = self.request("POST", "/api/start-branch", body="{}")
        self.assertEqual(status, 401)
        self.server.sessions["test-session"] = {
            "token": "fake", "user": "reviewer", "csrf": "csrf-test",
            "branch": "main", "created": time.time(),
        }
        cookie = {"Cookie": "nac_session=test-session"}
        status, headers, body = self.request("GET", "/api/status", headers=cookie)
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["branch"], "main")
        self.assertEqual(headers["Cache-Control"], "no-store")
        status, _, _ = self.request("POST", "/api/start-branch", body="{}", headers={
            **cookie, "Origin": "https://attacker.example", "X-Editor-Token": "csrf-test",
            "Content-Type": "application/json",
        })
        self.assertEqual(status, 403)

    def test_oauth_callback_requires_browser_bound_state(self):
        status, headers, _ = self.request("GET", "/login")
        self.assertEqual(status, 302)
        state = parse_qs(urlparse(headers["Location"]).query)["state"][0]
        self.assertIn("nac_oauth_state=", headers["Set-Cookie"])
        status, _, _ = self.request("GET", "/callback?state=" + state + "&code=fake")
        self.assertEqual(status, 401)

    def test_hosted_login_edit_preview_save_and_review_flow(self):
        class FakeStore:
            def slugs(self, ref):
                from case_editor_model import slugs
                return slugs()

            review_calls = []

            def __init__(self, owner, repo, token):
                self.token = token

            def create_branch(self, branch):
                return "ref-main"

            def load_case(self, slug, branch):
                model = load_case(slug)
                model["expected_ref"] = "ref-main"
                return model

            def preview(self, slug, branch, data):
                return {"changed": True, "changes": ["Bezeichnung geändert"], "case": slug}

            def save(self, slug, branch, data):
                return {"changed": True, "revision": data["revision"], "expected_ref": "ref-next"}

            def create_pr(self, slug, branch, reason, source):
                return "https://github.com/notariat8/ontology/pull/123"

            def list_case_reviews(self):
                return [{"number": 42, "case": "immobilienkaufvertrag", "title": "Fachliche Änderung"}]

            def review_detail(self, number):
                return {"number": number, "case": "immobilienkaufvertrag", "title": "Fachliche Änderung", "author": "author", "draft": False, "problem": "", "head_sha": "b" * 40, "changes": ["Bezeichnung geändert"], "body": "Fachlicher Grund", "url": "https://github.com/notariat8/ontology/pull/42"}

            def submit_case_review(self, number, head_sha, event, body, reviewer, notaries, checks):
                self.review_calls.append((number, head_sha, event, body, reviewer, notaries, checks))
                return "https://github.com/notariat8/ontology/pull/42#pullrequestreview-1"

        self.server.config["NOTARY_REVIEWERS"] = "reviewer"
        status, headers, _ = self.request("GET", "/login")
        self.assertEqual(status, 302)
        state = parse_qs(urlparse(headers["Location"]).query)["state"][0]
        with (
            patch("cloud_editor.urlopen", return_value=BytesIO(b'{"access_token":"fake-user-token"}')),
            patch("cloud_editor.github_json", side_effect=lambda url, token: {"login": "reviewer"} if url.endswith("/user") else {"full_name": "notariat8/ontology"}),
            patch("cloud_editor.GitHubStore", FakeStore),
        ):
            status, _, _ = self.request("GET", "/callback?state=" + state + "&code=fake", headers={"Cookie": "nac_oauth_state=" + state})
            self.assertEqual(status, 302)
            sid = next(iter(self.server.sessions))
            cookie = {"Cookie": "nac_session=" + sid}
            status, _, body = self.request("GET", "/api/status", headers=cookie)
            self.assertEqual(status, 200)
            csrf = json.loads(body)["token"]
            post_headers = {**cookie, "Origin": "https://editor.example.org", "X-Editor-Token": csrf, "Content-Type": "application/json"}
            status, _, body = self.request("POST", "/api/start-branch", body='{"case":"immobilienkaufvertrag"}', headers=post_headers)
            self.assertEqual(status, 200)
            self.assertTrue(json.loads(body)["branch"].startswith("codex/ontology-editor-reviewer-"))
            status, _, body = self.request("GET", "/api/cases/immobilienkaufvertrag", headers=cookie)
            self.assertEqual(status, 200)
            model = json.loads(body)
            self.assertEqual(model["expected_ref"], "ref-main")
            payload = json.dumps(model)
            status, _, _ = self.request("POST", "/api/cases/immobilienkaufvertrag/preview", body=payload, headers=post_headers)
            self.assertEqual(status, 200)
            status, _, body = self.request("POST", "/api/cases/immobilienkaufvertrag/save", body=payload, headers=post_headers)
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(body)["expected_ref"], "ref-next")
            review = json.dumps({"reason": "Fachliche Anpassung der Vorlage", "source": "NaC-Commit abc123"})
            status, _, body = self.request("POST", "/api/cases/immobilienkaufvertrag/review", body=review, headers=post_headers)
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(body)["branch"], "main")
            self.assertEqual(self.server.sessions[sid]["branch"], "main")
            status, _, body = self.request("GET", "/api/reviews", headers=cookie)
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(body)[0]["number"], 42)
            status, _, body = self.request("GET", "/api/reviews/42", headers=cookie)
            self.assertEqual(status, 200)
            self.assertTrue(json.loads(body)["can_approve"])
            decision = json.dumps({"head_sha": "b" * 40, "event": "APPROVE", "body": "Fachlich ausführlich geprüft", "checks": {"terms": True, "sources": True, "relations": True}})
            status, _, body = self.request("POST", "/api/reviews/42/review", body=decision, headers=post_headers)
            self.assertEqual(status, 200)
            self.assertIn("pullrequestreview", json.loads(body)["url"])
            self.assertEqual(FakeStore.review_calls[0][-2], {"reviewer"})
            self.assertTrue(FakeStore.review_calls[0][-1]["terms"])
            status, _, body = self.request("POST", "/api/logout", body="{}", headers=post_headers)
            self.assertEqual(status, 200)
            self.assertTrue(json.loads(body)["ok"])
            status, _, _ = self.request("GET", "/api/status", headers=cookie)
            self.assertEqual(status, 401)


if __name__ == "__main__":
    unittest.main()
