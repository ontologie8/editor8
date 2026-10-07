# SPDX-License-Identifier: AGPL-3.0-or-later
"""Prove tenant/data isolation and revocation without cloud credentials."""
from io import BytesIO
import hashlib
import http.client
import json
from pathlib import Path
import sys
import threading
import time
from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse
import unittest
from unittest.mock import Mock, patch

from cryptography.hazmat.primitives.asymmetric import rsa
import jwt

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from access_control import AccessControl, AccessDenied, AccessUnavailable, TableAccessStore
from cloud_editor import CloudHandler, CloudServer
from entra_identity import EntraIdentity
from github_store import GitHubStore

TENANT = "11111111-1111-4111-8111-111111111111"
CLIENT = "22222222-2222-4222-8222-222222222222"
OID = "33333333-3333-4333-8333-333333333333"


class PolicyFixture:
    def __init__(self):
        self.data = {"app_group": "app", "repositories": [
            {"repository": "example/notar", "label": "Notar", "groups": {"read": "nr", "write": "nw", "review": "nv", "merge": "nm"}},
            {"repository": "example/anwalt", "label": "Anwalt", "groups": {"read": "ar", "write": "aw"}}]}
        self.links = {42: TENANT + ":" + OID, 43: TENANT + ":44444444-4444-4444-8444-444444444444"}

    def policy(self):
        return self.data

    def principal_for_github(self, identifier):
        return self.links.get(identifier)

    def bind(self, principal, identifier):
        if self.links.get(identifier) != principal:
            raise AccessDenied("Konto bereits verknüpft")


class MembershipFixture:
    def __init__(self):
        self.groups = {"app", "nw", "ar"}

    def memberships(self, session, groups):
        return self.groups & set(groups)


class AccessTests(unittest.TestCase):
    def setUp(self):
        self.store, self.identity = PolicyFixture(), MembershipFixture()
        self.now = 100
        self.access = AccessControl(self.store, self.identity, clock=lambda: self.now)
        self.session = {"principal": TENANT + ":" + OID}

    def test_writer_in_one_repository_is_only_reader_in_the_other(self):
        self.access.require(self.session, "example/notar", "write")
        self.access.require(self.session, "example/anwalt", "read")
        with self.assertRaises(AccessDenied):
            self.access.require(self.session, "example/anwalt", "write")
        with self.assertRaises(AccessDenied):
            self.access.require(self.session, "example/hidden")
        self.assertEqual([entry["repository"] for entry in self.access.grants(self.session)], ["example/notar", "example/anwalt"])

    def test_repository_revocation_applies_within_sixty_seconds_and_immediately_on_write(self):
        self.access.require(self.session, "example/notar", "write")
        self.identity.groups.remove("nw")
        with self.assertRaises(AccessDenied):
            self.access.require(self.session, "example/notar", "write", force=True)
        self.assertEqual([entry["repository"] for entry in self.access.grants(self.session)], ["example/anwalt"])

    def test_app_revocation_expires_the_read_cache(self):
        self.access.grants(self.session)
        self.identity.groups.remove("app")
        self.now += 60
        with self.assertRaises(AccessDenied):
            self.access.grants(self.session)
        self.assertNotIn("access_cache", self.session)

    def test_policy_and_provider_failures_do_not_keep_stale_write_grants(self):
        self.access.grants(self.session)
        with patch.object(self.store, "policy", side_effect=TimeoutError("private-token")):
            with self.assertRaises(AccessUnavailable) as error:
                self.access.require(self.session, "example/notar", "write", force=True)
        self.assertNotIn("private-token", str(error.exception))
        self.assertNotIn("access_cache", self.session)

    def test_self_review_uses_the_verified_person_not_the_display_name(self):
        with self.assertRaises(AccessDenied):
            self.access.other_author(self.session, 42)
        self.assertNotEqual(self.access.other_author(self.session, 43), self.session["principal"])
        with self.assertRaises(AccessDenied):
            self.access.other_author(self.session, 999)

    def test_identity_link_cannot_be_rebound_or_shared(self):
        store = object.__new__(TableAccessStore)
        store.table = Mock()
        store.get = Mock(side_effect=[{"GithubId": "42"}, {"Principal": "same-person"}])
        store.bind("same-person", 42)
        store.table.submit_transaction.assert_not_called()
        store.get = Mock(side_effect=[{"GithubId": "41"}, {"Principal": "other-person"}])
        with self.assertRaises(AccessDenied):
            store.bind("same-person", 42)
        store.table.submit_transaction.assert_not_called()
        store.get = Mock(return_value=None)
        store.bind("verified-person", 43)
        operations = store.table.submit_transaction.call_args.args[0]
        self.assertEqual({operation[1]["PartitionKey"] for operation in operations}, {"links"})
        self.assertEqual(len(operations), 2)


class SignedTokenTests(unittest.TestCase):
    def setUp(self):
        self.identity = EntraIdentity(TENANT, CLIENT, "synthetic-secret", "https://editor.example")
        self.key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.claims = {"iss": self.identity.authority + "/v2.0", "aud": CLIENT, "exp": int(time.time()) + 60,
                       "iat": int(time.time()), "tid": TENANT, "oid": OID, "nonce": "expected-nonce", "roles": ["App.Use"]}

    def complete(self, claims, key=None):
        token = jwt.encode(claims, key or self.key, algorithm="RS256")
        app = Mock()
        app.acquire_token_by_auth_code_flow.return_value = {"access_token": "synthetic-token", "id_token": token, "id_token_claims": claims}
        with patch.object(self.identity, "application", return_value=app), patch.object(self.identity.keys, "get_signing_key_from_jwt", return_value=SimpleNamespace(key=self.key.public_key())):
            return self.identity.complete({"editor8_nonce": "expected-nonce"}, {"code": "synthetic-code"})

    def test_valid_signature_and_tenant_create_a_stable_principal(self):
        self.assertEqual(self.complete(self.claims)["principal"], TENANT + ":" + OID)

    def test_wrong_tenant_audience_issuer_nonce_expiry_and_assignment_are_rejected(self):
        for change in ({"tid": CLIENT}, {"aud": TENANT}, {"iss": "https://attacker.example"}, {"nonce": "other-nonce"}, {"exp": int(time.time()) - 1}, {"roles": []}):
            with self.subTest(change=change), self.assertRaises((jwt.PyJWTError, AccessDenied)):
                self.complete({**self.claims, **change})

    def test_a_signature_from_another_key_is_rejected(self):
        with self.assertRaises(jwt.InvalidSignatureError):
            self.complete(self.claims, rsa.generate_private_key(public_exponent=65537, key_size=2048))


class ProtectedRoutesTests(unittest.TestCase):
    def setUp(self):
        self.server = CloudServer(("127.0.0.1", 0), {"GITHUB_REPOSITORY": "example/notar", "PUBLIC_ORIGIN": "https://editor.example", "EDITOR_USERS": "legacy-only"})
        self.store, self.identity = PolicyFixture(), MembershipFixture()
        self.server.access = AccessControl(self.store, self.identity)
        self.session = {"principal": TENANT + ":" + OID, "created": time.time(), "user": "notary", "user_id": 42,
                        "token": "synthetic-token", "csrf": "csrf", "repository": "example/notar", "branch": "main",
                        "github_repository_cache": {"checked": time.time(), "token_key": hashlib.sha256(b"synthetic-token").hexdigest(), "repositories": {"example/notar", "example/anwalt"}}}
        self.server.sessions["session"] = self.session
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.cleanup)

    def cleanup(self):
        self.server.shutdown(); self.thread.join(); self.server.server_close()

    def request(self, path, data=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port)
        headers = {"Cookie": "nac_session=session", "Origin": "https://editor.example", "X-Editor-Token": "csrf"}
        if data is not None:
            headers["Content-Type"] = "application/json"
        connection.request("POST" if data is not None else "GET", path, json.dumps(data) if data is not None else None, headers)
        response = connection.getresponse()
        status, payload = response.status, json.loads(response.read())
        connection.close()
        return status, payload

    def test_hidden_public_repository_cannot_be_selected_even_when_github_is_readable(self):
        with patch("cloud_editor.github_json", return_value={"permissions": {"push": True}}):
            status, _ = self.request("/api/repositories/select", {"repository": "example/hidden"})
        self.assertEqual(status, 403)
        self.assertEqual(self.session["repository"], "example/notar")

    def test_github_read_does_not_become_write_through_an_entra_role(self):
        def provider(url, token):
            if "/user/installations?" in url:
                return {"installations": [{"id": 1}]}
            if "/installations/1/repositories?" in url:
                return {"repositories": [{"full_name": "example/notar"}]}
            return {"permissions": {"push": False}}
        with patch("cloud_editor.github_json", side_effect=provider), patch("cloud_editor.GitHubStore.create_branch") as write:
            status, _ = self.request("/api/start-branch", {"purpose": "case", "case": "demo"})
        self.assertEqual(status, 403)
        write.assert_not_called()

    def test_removed_writer_cannot_save_with_an_existing_session(self):
        self.server.access.grants(self.session)
        self.identity.groups.remove("nw")
        with patch("cloud_editor.GitHubStore.save") as write:
            status, _ = self.request("/api/cases/demo/save", {})
        self.assertEqual(status, 403)
        write.assert_not_called()

    def test_removed_app_user_is_denied_without_exposing_content_and_can_logout(self):
        self.identity.groups.remove("app")
        status, body = self.request("/api/cases")
        self.assertEqual(status, 403)
        self.assertNotIn("synthetic-token", json.dumps(body))
        self.assertEqual(self.request("/api/start-branch", {"purpose": "case"})[0], 403)
        self.assertEqual(self.request("/api/logout", {})[0], 200)

    def test_removed_installation_is_rechecked_before_a_write(self):
        with patch("cloud_editor.github_json", return_value={"installations": []}), patch("cloud_editor.GitHubStore.create_branch") as write:
            self.assertEqual(self.request("/api/start-branch", {"purpose": "case"})[0], 403)
        write.assert_not_called()

    def test_policy_outage_returns_a_safe_503_for_reads_and_writes(self):
        with patch.object(self.store, "policy", side_effect=TimeoutError("private-token")):
            for path, data in (("/api/cases", None), ("/api/start-branch", {"purpose": "case"})):
                with self.subTest(path=path):
                    status, body = self.request(path, data)
                    self.assertEqual(status, 503)
                    self.assertNotIn("private-token", json.dumps(body))


class LinkedLoginTests(unittest.TestCase):
    def setUp(self):
        self.server = CloudServer(("127.0.0.1", 0), {"GITHUB_APP_CLIENT_ID": "synthetic-client",
            "GITHUB_APP_CLIENT_SECRET": "synthetic-secret", "GITHUB_REPOSITORY": "example/notar",
            "PUBLIC_ORIGIN": "https://editor.example", "EDITOR_USERS": "legacy-only"})
        self.store, self.identity = PolicyFixture(), MembershipFixture()
        self.identity.begin = Mock(return_value={"state": "entra-state", "auth_uri": "https://login.microsoftonline.com/synthetic?state=entra-state"})
        self.identity.complete = Mock(return_value={"principal": TENANT + ":" + OID})
        self.server.identity = self.identity
        self.server.access = AccessControl(self.store, self.identity)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.cleanup)

    def cleanup(self):
        self.server.shutdown(); self.thread.join(); self.server.server_close()

    def request(self, path, cookie=""):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        connection.request("GET", path, headers={"Host": "editor.example", "Cookie": cookie})
        response = connection.getresponse()
        result = response.status, response.getheaders(), response.read().decode()
        connection.close()
        return result

    def github_step(self):
        self.assertEqual(self.request("/login")[0], 302)
        status, headers, _ = self.request("/entra/callback?state=entra-state&code=synthetic", "entra_oauth_state=entra-state")
        self.assertEqual(status, 302)
        cookies = dict(header.split(";", 1)[0].split("=", 1) for name, header in headers if name.lower() == "set-cookie")
        target = next(value for name, value in headers if name.lower() == "location")
        self.assertEqual(parse_qs(urlparse(target).query)["code_challenge_method"], ["S256"])
        return cookies, dict(self.server.pending[cookies["nac_oauth_state"]])

    def callback(self, cookies):
        return self.request("/callback?state=" + cookies["nac_oauth_state"] + "&code=synthetic-code",
                            "; ".join(key + "=" + value for key, value in cookies.items()))

    def test_two_verified_logins_bind_and_rotate_the_session_without_a_static_user_list(self):
        cookies, pending = self.github_step()
        def provider(url, token):
            if url.endswith("/user"):
                return {"login": "notary", "id": 42}
            if "/user/installations?" in url:
                return {"installations": [{"id": 1}]}
            if "/installations/1/repositories?" in url:
                return {"repositories": [{"full_name": "example/notar"}]}
            return {"permissions": {"push": True}}
        with patch("cloud_editor.urlopen", return_value=BytesIO(b'{"access_token":"synthetic-token"}')), patch("cloud_editor.github_json", side_effect=provider), patch.object(self.store, "bind", wraps=self.store.bind) as link:
            status, headers, body = self.callback(cookies)
        self.assertEqual(status, 302)
        link.assert_called_once_with(TENANT + ":" + OID, 42)
        self.assertNotIn(pending["identity_sid"], self.server.sessions)
        session = next(iter(self.server.sessions.values()))
        self.assertEqual(session["user"], "notary")
        self.assertEqual(session["repository"], "example/notar")
        self.assertNotIn("synthetic-token", body + str(headers))
        self.assertEqual(self.callback(cookies)[0], 401)

    def test_another_browser_cannot_attach_github_to_the_entra_identity(self):
        self.request("/login")
        self.assertEqual(self.request("/entra/callback?state=entra-state&code=synthetic")[0], 403)
        self.identity.complete.assert_not_called()
        cookies, _ = self.github_step()
        cookies["nac_session"] = "different-browser"
        with patch("cloud_editor.urlopen") as exchange:
            self.assertEqual(self.callback(cookies)[0], 401)
        exchange.assert_not_called()

    def test_revocation_between_provider_logins_prevents_linking_and_token_exchange(self):
        cookies, _ = self.github_step()
        self.identity.groups.remove("app")
        with patch("cloud_editor.urlopen") as exchange, patch.object(self.store, "bind") as link:
            self.assertEqual(self.callback(cookies)[0], 403)
        exchange.assert_not_called(); link.assert_not_called()


class MergeTests(unittest.TestCase):
    def setUp(self):
        self.store = GitHubStore("example", "data", "synthetic-token")
        self.head = "a" * 40
        self.detail = {"head_sha": self.head, "author_id": 42, "draft": False, "problem": ""}
        self.review = {"id": 7, "user": {"id": 43}, "state": "APPROVED", "commit_id": self.head}

    def merge(self, *, head=None, approved=True, state="APPROVED", check="success"):
        def provider(method, path, data=None):
            if path.startswith("/pulls/1/reviews"):
                return [{**self.review, "state": state}]
            if path.endswith("/check-runs?per_page=100"):
                return {"total_count": 1, "check_runs": [{"status": "completed", "conclusion": check}]}
            if path.endswith("/status"):
                return {"statuses": [], "state": "pending"}
            if path == "/pulls/1/merge":
                return {"merged": True, "sha": "b" * 40}
            raise AssertionError(path)
        with patch.object(self.store, "review_detail", return_value=self.detail), patch.object(self.store, "request", side_effect=provider) as request:
            try:
                result = self.store.merge_case_review(1, head or self.head, lambda *args: approved)
            finally:
                self.writes = [call for call in request.call_args_list if call.args[0] == "PUT"]
        return result

    def test_merge_is_bound_to_the_reviewed_head_and_an_editor_receipt(self):
        self.assertTrue(self.merge()["merged"])
        self.assertEqual(self.writes[0].args[2]["sha"], self.head)

    def test_stale_head_missing_receipt_change_request_and_failed_checks_block_merge(self):
        for args in ({"head": "c" * 40}, {"approved": False}, {"state": "REQUEST_CHANGES"}, {"check": "failure"}):
            with self.subTest(args=args), self.assertRaises(ValueError):
                self.merge(**args)
            self.assertEqual(self.writes, [])
