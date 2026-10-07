# SPDX-License-Identifier: AGPL-3.0-or-later
"""Single-instance editor with operator admission and personal GitHub data access.

AUTH_PROVIDER=entra uses signed Entra identity, runtime groups and verified
GitHub account links. The previous github provider remains available for a
controlled migration, until the central permissions have been provisioned.
TLS terminates at the trusted hosting proxy. Sessions are kept in memory and
expire after eight hours; a restart signs editors out without losing Git data.
"""

from __future__ import annotations

import argparse
from contextlib import nullcontext
import base64
from datetime import datetime, timezone
import hashlib
from html import escape
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import secrets
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, quote, urlencode, urlparse
from urllib.request import Request, urlopen

from rdflib import Graph, Namespace
from rdflib.namespace import SKOS

from data_contract import APP_ROOT
from brand_assets import BRAND_ASSETS
from learning_assets import LEARNING_ASSETS
from release_info import release_info
from repository_registry import load_repositories
from github_store import GitHubError, GitHubStore
from usage_audit import audit_line, response_action
from access_control import AccessControl, AccessDenied, AccessUnavailable, TableAccessStore
from entra_identity import EntraIdentity


ASSETS = APP_ROOT / "editor"
MAX_REQUEST = 250_000
SESSION_LIFETIME = 8 * 60 * 60
AUTH_LIFETIME = 5 * 60


class AuthenticationRejected(PermissionError):
    """A fixed editor message safe to show on the sign-in error page."""


def require_config() -> dict[str, str]:
    names = ("GITHUB_APP_CLIENT_ID", "GITHUB_APP_CLIENT_SECRET", "GITHUB_REPOSITORY", "PUBLIC_ORIGIN")
    config = {name: os.environ.get(name, "") for name in names}
    config["AUTH_PROVIDER"] = os.environ.get("AUTH_PROVIDER", "github")
    if config["AUTH_PROVIDER"] not in {"github", "entra"}:
        raise ValueError("Ungültiger Anmeldeanbieter")
    config["EDITOR_USERS"] = os.environ.get("EDITOR_USERS", "")
    if config["AUTH_PROVIDER"] == "entra":
        for name in ("ENTRA_TENANT_ID", "ENTRA_CLIENT_ID", "ENTRA_CLIENT_SECRET", "IAM_TABLE_ENDPOINT"):
            config[name] = os.environ.get(name, "")
            if not config[name]:
                raise ValueError("Entra-Konfiguration und Berechtigungsdienst fehlen")
    config["NOTARY_REVIEWERS"] = os.environ.get("NOTARY_REVIEWERS", "")
    config["ONTOLOGY_MAINTAINERS"] = os.environ.get("ONTOLOGY_MAINTAINERS", "")
    if any(not config[name] for name in names):
        raise ValueError("GitHub-App-Konfiguration und PUBLIC_ORIGIN fehlen")
    origin = urlparse(config["PUBLIC_ORIGIN"])
    if origin.scheme != "https" or not origin.netloc or origin.path not in ("", "/") or origin.query or origin.fragment or origin.username or origin.password:
        raise ValueError("PUBLIC_ORIGIN muss eine HTTPS-Ursprungsadresse sein")
    owner_repo = config["GITHUB_REPOSITORY"].split("/")
    if len(owner_repo) != 2:
        raise ValueError("GITHUB_REPOSITORY muss owner/repo sein")
    GitHubStore(owner_repo[0], owner_repo[1], "configuration-check")
    config["DATA_REPOSITORIES"] = load_repositories()
    if not any(entry["repository"] == config["GITHUB_REPOSITORY"] for entry in config["DATA_REPOSITORIES"]):
        raise ValueError("Das Standardrepository fehlt in config/data-repositories.json")
    if config["AUTH_PROVIDER"] == "entra":
        return config
    if not all(value.strip() for value in config["EDITOR_USERS"].split(",")):
        raise ValueError("EDITOR_USERS muss GitHub-Benutzernamen enthalten")
    editors = {value.strip().lower() for value in config["EDITOR_USERS"].split(",")}
    notaries = {value.strip().lower() for value in config["NOTARY_REVIEWERS"].split(",") if value.strip()}
    if notaries - editors:
        raise ValueError("NOTARY_REVIEWERS muss eine Teilmenge von EDITOR_USERS sein")
    maintainers = {value.strip().lower() for value in config["ONTOLOGY_MAINTAINERS"].split(",") if value.strip()}
    if maintainers - editors:
        raise ValueError("ONTOLOGY_MAINTAINERS muss eine Teilmenge von EDITOR_USERS sein")
    return config


def github_json(url: str, token: str) -> dict:
    req = Request(url, headers={
        "Accept": "application/vnd.github+json", "Authorization": "Bearer " + token,
        "User-Agent": "NaC-ontology-editor", "X-GitHub-Api-Version": "2026-03-10",
    })
    with urlopen(req, timeout=20) as response:
        return json.load(response)


class CloudServer(ThreadingHTTPServer):
    def __init__(self, address: tuple[str, int], config: dict[str, str]):
        super().__init__(address, CloudHandler)
        self.config = config
        self.sessions: dict[str, dict] = {}
        self.pending: dict[str, dict] = {}
        self.impact_cache: tuple[str, dict] | None = None
        self.case_index_cache: tuple[str, dict] | None = None
        self.lock = threading.RLock()
        self.owner, self.repo = config["GITHUB_REPOSITORY"].split("/")
        self.repositories = config.get("DATA_REPOSITORIES", [{"repository": config["GITHUB_REPOSITORY"], "label": config["GITHUB_REPOSITORY"]}])
        self.identity = None
        self.access = None
        if config.get("AUTH_PROVIDER") == "entra":
            self.identity = EntraIdentity(config["ENTRA_TENANT_ID"], config["ENTRA_CLIENT_ID"], config["ENTRA_CLIENT_SECRET"], config["PUBLIC_ORIGIN"])
            self.access = AccessControl(TableAccessStore(config["IAM_TABLE_ENDPOINT"]), self.identity)


class CloudHandler(BaseHTTPRequestHandler):
    server: CloudServer

    def log_request(self, code: int | str = "-", size: int | str = "-") -> None:
        # The OAuth callback query contains a one-time code. Application
        # request logs record only the path; the proxy needs the same policy.
        self.log_message("%s %s %s %s", self.command, urlparse(self.path).path, code, size)

    def _send(self, status: int, body: bytes, kind: str, extra: dict[str, str] | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", kind + "; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        ancestors = "'self'" if urlparse(self.path).path in LEARNING_ASSETS else "'none'"
        self.send_header("Content-Security-Policy", f"default-src 'self'; style-src 'self'; script-src 'self'; base-uri 'none'; frame-ancestors {ancestors}; form-action 'none'")
        for key, value in (extra or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: int, payload: dict | list) -> None:
        action = response_action(self.command, urlparse(self.path).path, status)
        if action:
            self._audit(action, status=status, changed=payload.get("changed") if isinstance(payload, dict) else None)
        self._send(status, json.dumps(payload, ensure_ascii=False).encode("utf-8"), "application/json")

    def _audit(self, action: str, *, status: int = 200, changed: bool | None = None) -> None:
        print(audit_line(action, getattr(self, "_audit_session", None), status=status, changed=changed, release=release_info()["commit"]), flush=True)

    def _redirect(self, target: str, cookies: list[str] | None = None) -> None:
        self.send_response(302)
        self.send_header("Location", target)
        self.send_header("Cache-Control", "no-store")
        for cookie in cookies or []:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()

    def _session(self, validate=True) -> dict:
        jar = SimpleCookie()
        try:
            jar.load(self.headers.get("Cookie", ""))
            sid = jar["nac_session"].value if "nac_session" in jar else ""
        except Exception:
            sid = ""
        with self.server.lock:
            session = self.server.sessions.get(sid)
            if not session or time.time() - session["created"] >= SESSION_LIFETIME:
                self.server.sessions.pop(sid, None)
                raise PermissionError("Bitte erneut anmelden")
        self._audit_session = session
        if validate and self.server.access:
            self.server.access.grants(session)
            if not session.get("user"):
                raise PermissionError("Bitte das GitHub-Konto verknüpfen")
        return session

    def _store(self, session: dict) -> GitHubStore:
        repository = session.get("repository", self.server.config["GITHUB_REPOSITORY"])
        self._repository(repository, session["user"], session)
        if self.server.access and repository not in self._github_repositories(session, session["token"]):
            raise AccessDenied("Die GitHub-App ist für diesen Bestand nicht freigegeben.")
        owner, repo = repository.split("/")
        return GitHubStore(owner, repo, session["token"])

    def _request_lock(self):
        try:
            # Authentication and provider failures belong inside _get/_post,
            # where they become a safe HTTP response. Lock lookup does no I/O.
            session = self._session(validate=False)
        except PermissionError:
            return nullcontext()
        with self.server.lock:
            return session.setdefault("request_lock", threading.RLock())

    def _repository(self, repository: str, username: str, session=None) -> dict:
        if self.server.access:
            return self.server.access.require(session or self._session(), repository)
        for entry in self.server.repositories:
            if entry["repository"] == repository and ("users" not in entry or username.lower() in {user.lower() for user in entry["users"]}):
                return entry
        raise ValueError("Dieses Datenrepository ist nicht freigeschaltet")

    def _available_repositories(self, username: str, token: str, session=None) -> list[dict]:
        available = []
        entries = self.server.access.grants(session) if self.server.access else self.server.repositories
        installed = self._github_repositories(session, token) if self.server.access else None
        for entry in entries:
            if installed is not None and entry["repository"] not in installed:
                continue
            try:
                self._repository(entry["repository"], username, session)
            except ValueError:
                continue
            try:
                github_json("https://api.github.com/repos/" + entry["repository"], token)
            except HTTPError as error:
                if error.code in (403, 404):
                    continue
                raise
            available.append({"repository": entry["repository"], "label": entry["label"]})
        return available

    def _github_repositories(self, session, token, force=False):
        cached = session.get("github_repository_cache")
        token_key = hashlib.sha256(token.encode()).hexdigest()
        if not force and cached and cached.get("token_key") == token_key and time.time() - cached["checked"] < 60:
            return cached["repositories"]
        repositories = set()
        for page in range(1, 11):
            response = github_json(f"https://api.github.com/user/installations?per_page=100&page={page}", token)
            installations = response["installations"]
            for installation in installations:
                if installation.get("suspended_at"):
                    continue
                identifier = installation["id"]
                if not isinstance(identifier, int) or isinstance(identifier, bool) or identifier <= 0:
                    raise ValueError("Ungültige GitHub-Installation")
                for repo_page in range(1, 11):
                    items = github_json(f"https://api.github.com/user/installations/{identifier}/repositories?per_page=100&page={repo_page}", token)["repositories"]
                    repositories.update(item["full_name"] for item in items)
                    if len(items) < 100:
                        break
                else:
                    raise AccessUnavailable("Die GitHub-Bestandsrechte sind nicht vollständig verfügbar.")
            if len(installations) < 100:
                break
        else:
            raise AccessUnavailable("Die GitHub-Installationen sind nicht vollständig verfügbar.")
        session["github_repository_cache"] = {"checked": time.time(), "repositories": repositories, "token_key": token_key}
        return repositories

    def _require_action(self, session, role):
        if self.server.access:
            repository = session["repository"]
            self.server.access.require(session, repository, role, force=True)
            if repository not in self._github_repositories(session, session["token"], force=True):
                raise AccessDenied("Die GitHub-App ist für diesen Bestand nicht freigegeben.")
            metadata = github_json("https://api.github.com/repos/" + repository, session["token"])
            if (metadata.get("permissions") or {}).get("push") is not True:
                raise AccessDenied("GitHub-Schreibrechte für diesen Bestand fehlen.")

    def _role(self, field: str) -> set[str]:
        session = self._session()
        repository = session.get("repository", self.server.config["GITHUB_REPOSITORY"])
        if self.server.access:
            entry = self.server.access.require(session, repository)
            role = {"NOTARY_REVIEWERS": "review", "ONTOLOGY_MAINTAINERS": "maintain"}[field]
            return {session["user"].lower()} if role in entry["roles"] else set()
        entry = self._repository(repository, session["user"])
        if field.lower() in entry:
            return {name.lower() for name in entry[field.lower()]}
        if repository != self.server.config["GITHUB_REPOSITORY"]:
            return set()
        return {name.strip().lower() for name in self.server.config.get(field, "").split(",") if name.strip()}

    def _notaries(self) -> set[str]:
        return self._role("NOTARY_REVIEWERS")

    def _maintainers(self) -> set[str]:
        return self._role("ONTOLOGY_MAINTAINERS")

    def _login(self) -> None:
        # A host-only OAuth cookie must be set on the callback's origin.
        origin = self.server.config["PUBLIC_ORIGIN"].rstrip("/")
        hostname = urlparse("//" + self.headers.get("Host", "")).hostname
        if hostname and hostname not in (urlparse(origin).hostname, "127.0.0.1", "localhost", "::1"):
            self._redirect(origin + "/login")
            return
        if self.server.identity:
            flow = self.server.identity.begin()
            state = flow["state"]
            with self.server.lock:
                now = time.time()
                self.server.pending = {key: value for key, value in self.server.pending.items() if now - value["created"] < AUTH_LIFETIME}
                if len(self.server.pending) >= 100:
                    raise ValueError("Zu viele laufende Anmeldungen")
                self.server.pending[state] = {"created": now, "entra_flow": flow}
            self._redirect(flow["auth_uri"], [f"entra_oauth_state={state}; Path=/entra/callback; Max-Age={AUTH_LIFETIME}; HttpOnly; Secure; SameSite=Lax"])
            return
        self._github_login()

    def _github_login(self, identity_sid=None):
        state = secrets.token_urlsafe(24)
        verifier = secrets.token_urlsafe(48)
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
        with self.server.lock:
            now = time.time()
            self.server.pending = {key: value for key, value in self.server.pending.items() if now - value["created"] < AUTH_LIFETIME}
            self.server.sessions = {key: value for key, value in self.server.sessions.items() if now - value["created"] < SESSION_LIFETIME}
            if len(self.server.pending) >= 100:
                raise ValueError("Zu viele laufende Anmeldungen. Bitte später erneut versuchen.")
            self.server.pending[state] = {"verifier": verifier, "created": time.time(), "identity_sid": identity_sid}
        params = {
            "client_id": self.server.config["GITHUB_APP_CLIENT_ID"],
            "redirect_uri": self.server.config["PUBLIC_ORIGIN"].rstrip("/") + "/callback",
            "state": state, "code_challenge": challenge, "code_challenge_method": "S256",
        }
        cookies = [f"nac_oauth_state={state}; Path=/callback; Max-Age={AUTH_LIFETIME}; HttpOnly; Secure; SameSite=Lax"]
        if identity_sid:
            cookies.extend([f"nac_session={identity_sid}; Path=/; Max-Age={SESSION_LIFETIME}; HttpOnly; Secure; SameSite=Lax",
                            "entra_oauth_state=; Path=/entra/callback; Max-Age=0; HttpOnly; Secure; SameSite=Lax"])
        self._redirect("https://github.com/login/oauth/authorize?" + urlencode(params), cookies)

    def _entra_callback(self, query):
        self._auth_stage = "entra-browser-state"
        try:
            state = query.get("state", [""])[0]
            jar = SimpleCookie()
            jar.load(self.headers.get("Cookie", ""))
            if not state or "entra_oauth_state" not in jar or jar["entra_oauth_state"].value != state:
                raise AccessDenied("Anmeldung stimmt nicht mit diesem Browser überein")
            with self.server.lock:
                pending = self.server.pending.pop(state, None)
            if not pending or "entra_flow" not in pending or time.time() - pending["created"] > AUTH_LIFETIME:
                raise AccessDenied("Anmeldung abgelaufen. Bitte erneut beginnen.")
            self._auth_stage = "entra-confirm"
            session = self.server.identity.complete(pending["entra_flow"], {key: value[0] for key, value in query.items()})
            self.server.access.grants(session, force=True)
            session.update(created=time.time(), csrf=secrets.token_urlsafe(32), branch="main")
            sid = secrets.token_urlsafe(32)
            with self.server.lock:
                self.server.sessions[sid] = session
            self._github_login(sid)
        except AccessDenied as error:
            self._auth_failure(403, str(error), "entra-rejected")
        except Exception:
            self._auth_failure(503, "Die Betreiberanmeldung konnte nicht geprüft werden. Bitte erneut anmelden.", "entra-unavailable")

    def _callback(self, query: dict[str, list[str]]) -> None:
        self._auth_stage = "browser-state"
        try:
            self._authorize(query)
        except AuthenticationRejected as error:
            self._auth_failure(401, str(error), "rejected")
        except AccessDenied as error:
            self._auth_failure(403, str(error), "access-rejected")
        except AccessUnavailable as error:
            self._auth_failure(503, str(error), "access-unavailable")
        except HTTPError as error:
            message = "GitHub konnte die Anmeldung nicht bestätigen. Bitte die Anmeldung erneut beginnen."
            self._auth_failure(503 if error.code >= 500 or error.code == 429 else 403, message, "github-http-" + str(error.code))
        except (URLError, TimeoutError, OSError) as error:
            category = "github-connection"
            if isinstance(error, TimeoutError) or isinstance(getattr(error, "reason", None), TimeoutError):
                category = "github-timeout"
            self._auth_failure(503, "Die Verbindung zu GitHub ist fehlgeschlagen. Bitte die Anmeldung erneut beginnen.", category)
        except (ValueError, KeyError, TypeError):
            self._auth_failure(502, "GitHub hat keine gültige Antwort für die Anmeldung geliefert. Bitte die Anmeldung erneut beginnen.", "invalid-response")
        except Exception:
            self._auth_failure(500, "Die Anmeldung konnte nicht abgeschlossen werden. Bitte die Anmeldung erneut beginnen und bei erneutem Fehler die Diagnose-Kennung melden.", "internal-error")

    def _auth_failure(self, status: int, message: str, category: str) -> None:
        request_id = secrets.token_hex(6)
        # Never log exception text, provider response bodies, URLs or credentials.
        self.log_message("auth_failure id=%s stage=%s category=%s status=%s", request_id, self._auth_stage, category, status)
        self._audit("login_denied", status=status)
        login = self.server.config["PUBLIC_ORIGIN"].rstrip("/") + "/login"
        body = (
            '<!doctype html><html lang="de"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>Anmeldung – editor8</title><link rel="stylesheet" href="/style.css"></head>'
            '<body class="auth-page"><main class="auth-card">'
            '<img src="/assets/brand/e8_192.png" width="48" height="48" alt="e8">'
            '<h1>Anmeldung nicht abgeschlossen</h1><p>' + escape(message) + '</p>'
            '<a class="auth-retry" href="' + escape(login, quote=True) + '">Erneut anmelden</a>'
            '<p class="auth-diagnostic">Diagnose-Kennung: <code>' + request_id + '</code></p>'
            '<p>Bei Rückfragen nur die Fehlermeldung und Diagnose-Kennung weitergeben.</p>'
            '</main></body></html>'
        )
        self._send(status, body.encode("utf-8"), "text/html", {
            "X-Request-ID": request_id,
            "Set-Cookie": "nac_oauth_state=; Path=/callback; Max-Age=0; HttpOnly; Secure; SameSite=Lax",
        })

    def _authorize(self, query: dict[str, list[str]]) -> None:
        state = query.get("state", [""])[0]
        code = query.get("code", [""])[0]
        jar = SimpleCookie()
        jar.load(self.headers.get("Cookie", ""))
        if not state or "nac_oauth_state" not in jar or jar["nac_oauth_state"].value != state:
            raise AuthenticationRejected("Anmeldung stimmt nicht mit diesem Browser überein")
        with self.server.lock:
            pending = self.server.pending.pop(state, None)
        if not pending or time.time() - pending["created"] > AUTH_LIFETIME or not code:
            raise AuthenticationRejected("Anmeldung abgelaufen. Bitte erneut beginnen.")
        identity_session = None
        if self.server.access:
            sid = pending.get("identity_sid")
            if not sid or "nac_session" not in jar or jar["nac_session"].value != sid:
                raise AuthenticationRejected("Bitte zuerst über den Betreiber anmelden")
            with self.server.lock:
                identity_session = self.server.sessions.get(sid)
            if not identity_session or time.time() - identity_session["created"] >= SESSION_LIFETIME:
                raise AuthenticationRejected("Betreiberanmeldung abgelaufen")
            self.server.access.grants(identity_session, force=True)
        self._auth_stage = "token-exchange"
        params = {
            "client_id": self.server.config["GITHUB_APP_CLIENT_ID"],
            "client_secret": self.server.config["GITHUB_APP_CLIENT_SECRET"],
            "code": code,
            "redirect_uri": self.server.config["PUBLIC_ORIGIN"].rstrip("/") + "/callback",
            "code_verifier": pending["verifier"],
        }
        req = Request("https://github.com/login/oauth/access_token", data=urlencode(params).encode(), headers={
            "Accept": "application/json", "User-Agent": "NaC-ontology-editor",
        }, method="POST")
        with urlopen(req, timeout=20) as response:
            result = json.load(response)
        token = result.get("access_token")
        if not token:
            errors = {
                "bad_verification_code": "Der Anmeldecode ist abgelaufen oder wurde bereits verwendet. Bitte die Anmeldung erneut beginnen.",
                "incorrect_client_credentials": "Die GitHub-App-Konfiguration muss vom Betreiber geprüft werden.",
                "redirect_uri_mismatch": "Die Callback-Adresse der GitHub-App muss vom Betreiber geprüft werden.",
                "bad_code_verifier": "Die Anmeldedaten passen nicht zu dieser Anmeldung. Bitte erneut beginnen.",
            }
            raise AuthenticationRejected(errors.get(result.get("error"), "GitHub-Anmeldung fehlgeschlagen. Bitte erneut beginnen."))
        self._auth_stage = "github-user"
        user = github_json("https://api.github.com/user", token)
        if not self.server.access:
            allowed = {name.strip().lower() for name in self.server.config["EDITOR_USERS"].split(",")}
            if user["login"].lower() not in allowed:
                raise AuthenticationRejected("Dieses GitHub-Konto ist nicht als Editor freigeschaltet")
        # A readable repo and a working user token are required; write permission
        # is enforced again by GitHub when creating branches or commits.
        self._auth_stage = "repository-access"
        available = self._available_repositories(user["login"], token, identity_session)
        if not available:
            raise AuthenticationRejected("Kein freigeschaltetes Datenrepository ist für dieses Konto zugänglich")
        if self.server.access:
            self.server.access.store.bind(identity_session["principal"], user.get("id"))
        default = self.server.config["GITHUB_REPOSITORY"]
        repository = default if any(entry["repository"] == default for entry in available) else available[0]["repository"]
        self._auth_stage = "session-create"
        sid = secrets.token_urlsafe(32)
        with self.server.lock:
            self.server.sessions[sid] = {
                **(identity_session or {}),
                "token": token, "user": user["login"], "user_id": user.get("id"), "csrf": secrets.token_urlsafe(32),
                "branch": "main", "repository": repository, "created": time.time(),
            }
            if pending.get("identity_sid"):
                self.server.sessions.pop(pending["identity_sid"], None)
            self._audit_session = self.server.sessions[sid]
        self._audit("login")
        self._redirect("/", [
            f"nac_session={sid}; Path=/; Max-Age={SESSION_LIFETIME}; HttpOnly; Secure; SameSite=Lax",
            "nac_oauth_state=; Path=/callback; Max-Age=0; HttpOnly; Secure; SameSite=Lax",
        ])

    def _catalog(self, catalog_text: str, case_ids: list[str]) -> list[dict]:
        graph = Graph().parse(data=catalog_text, format="turtle")
        n8 = Namespace("https://notariat8.github.io/ontology/id/")
        return [{"slug": slug, "title": str(graph.value(n8[f"vorgangsart-{slug}"], SKOS.prefLabel))} for slug in case_ids]

    def do_GET(self) -> None:
        with self._request_lock():
            self._get()

    def _get(self) -> None:
        self._audit_session = None
        try:
            path = urlparse(self.path)
            if path.path == "/healthz":
                self._json(200, {"status": "ok"})
            elif path.path == "/api/release":
                self._json(200, release_info())
            elif path.path == "/login":
                self._login()
            elif path.path == "/callback":
                self._callback(parse_qs(path.query))
            elif path.path == "/entra/callback" and self.server.identity:
                self._entra_callback(parse_qs(path.query))
            elif path.path in ("/", "/index.html", "/app.js", "/interaction.js", "/recovery.js", "/comparison.js", "/style.css"):
                filename = "index.html" if path.path == "/" else path.path.lstrip("/")
                kind = {"index.html": "text/html", "app.js": "text/javascript", "interaction.js": "text/javascript", "recovery.js": "text/javascript", "comparison.js": "text/javascript", "style.css": "text/css"}
                self._send(200, (ASSETS / filename).read_bytes(), kind[filename])
            elif path.path in BRAND_ASSETS:
                self._send(200, (ASSETS / BRAND_ASSETS[path.path]).read_bytes(), "image/png")
            elif path.path in LEARNING_ASSETS:
                filename, kind = LEARNING_ASSETS[path.path]
                self._send(200, (ASSETS / filename).read_bytes(), kind)
            elif path.path == "/api/status":
                session = self._session()
                roles = self.server.access.require(session, session["repository"])["roles"] if self.server.access else {"write"}
                self._json(200, {"token": session["csrf"], "branch": session["branch"], "purpose": session.get("purpose", "case"), "case": session.get("case", ""), "hosted": True, "user": session["user"], "can_edit": "write" in roles, "auth_provider": "entra" if self.server.access else "github", "notary_reviewer": session["user"].lower() in self._notaries(), "ontology_maintainer": session["user"].lower() in self._maintainers()})
            elif path.path == "/api/repositories":
                session = self._session()
                self._json(200, {"selected": session.get("repository", self.server.config["GITHUB_REPOSITORY"]), "repositories": self._available_repositories(session["user"], session["token"], session)})
            elif path.path == "/api/drafts":
                session = self._session()
                drafts = self._store(session).list_drafts(session["user"])
                if session["user"].lower() not in self._maintainers():
                    drafts = [item for item in drafts if item["purpose"] == "case"]
                self._json(200, drafts)
            elif path.path == "/api/cases":
                session = self._session()
                store = self._store(session)
                main_ref = store.ref("main")
                self._json(200, self._catalog(store.read_file("catalog/nac-usecases.ttl", main_ref), store.slugs(main_ref)))
            elif path.path == "/api/case-index":
                session = self._session()
                store = self._store(session)
                main_ref = store.ref("main")
                with self.server.lock:
                    cached = self.server.case_index_cache
                cache_key = (session.get("repository", self.server.config["GITHUB_REPOSITORY"]), session["user"], main_ref)
                if cached and cached[0] == cache_key:
                    index = cached[1]
                else:
                    index = store.case_index(main_ref)
                    with self.server.lock:
                        self.server.case_index_cache = (cache_key, index)
                self._json(200, index)
            elif path.path == "/api/reviews":
                session = self._session()
                self._json(200, self._store(session).list_case_reviews())
            elif path.path.startswith("/api/reviews/") and path.path.count("/") == 3:
                session = self._session()
                number = int(path.path.rsplit("/", 1)[1])
                detail = self._store(session).review_detail(number)
                detail["can_review"] = session["user"].lower() != detail["author"].lower() and not detail["draft"]
                detail["can_approve"] = session["user"].lower() in self._notaries() and session["user"].lower() != detail["author"].lower() and not detail["draft"] and not detail["problem"]
                detail["can_merge"] = False
                if self.server.access:
                    roles = self.server.access.require(session, session["repository"])["roles"]
                    detail["can_review"] = detail["can_review"] and "review" in roles
                    try:
                        self.server.access.other_author(session, detail.get("author_id"))
                    except (AccessDenied, ValueError):
                        detail["can_approve"] = False
                    detail["can_merge"] = "merge" in roles and not detail["draft"] and not detail["problem"]
                self._json(200, detail)
            elif path.path == "/api/vocabulary":
                session = self._session()
                branch = session["branch"] if session.get("purpose") == "vocabulary" else "main"
                self._json(200, self._store(session).load_vocabulary(branch))
            elif path.path == "/api/vocabulary/impact":
                session = self._session()
                store = self._store(session)
                main_ref = store.ref("main")
                with self.server.lock:
                    cached = self.server.impact_cache
                cache_key = (session.get("repository", self.server.config["GITHUB_REPOSITORY"]), session["user"], main_ref)
                if cached and cached[0] == cache_key:
                    impact = cached[1]
                else:
                    impact = store.vocabulary_impact(main_ref)
                    with self.server.lock:
                        self.server.impact_cache = (cache_key, impact)
                self._json(200, impact)
            elif path.path == "/api/vocabulary/turtle":
                session = self._session()
                branch = session["branch"] if session.get("purpose") == "vocabulary" else "main"
                self._json(200, {"turtle": self._store(session).read_file("ontology/core.ttl", branch)})
            elif path.path.startswith("/api/cases/") and path.path.count("/") == 3:
                session = self._session()
                slug = path.path.rsplit("/", 1)[1]
                branch = session["branch"] if session.get("purpose", "case") == "case" and session.get("case") == slug else "main"
                self._json(200, self._store(session).load_case(slug, branch))
            elif path.path.startswith("/api/cases/") and path.path.endswith("/history") and path.path.count("/") == 4:
                session = self._session()
                slug = path.path.split("/")[3]
                self._json(200, self._store(session).case_history(slug))
            elif path.path.startswith("/api/cases/") and path.path.endswith("/turtle") and path.path.count("/") == 4:
                session = self._session()
                slug = path.path.split("/")[3]
                if slug not in self._store(session).slugs("main"):
                    raise ValueError("Unbekannter Fall")
                branch = session["branch"] if session.get("purpose", "case") == "case" and session.get("case") == slug else "main"
                self._json(200, {"turtle": self._store(session).read_file(f"cases/{slug}/ontology.ttl", branch)})
            else:
                self._json(404, {"error": "Nicht gefunden"})
        except AccessDenied as error:
            self._json(403, {"error": str(error)})
        except AccessUnavailable as error:
            self._json(503, {"error": str(error)})
        except PermissionError as error:
            self._json(401, {"error": str(error)})
        except GitHubError as error:
            self._json(401 if error.status == 401 else 403 if error.status == 403 else 400, {"error": str(error)})
        except ValueError as error:
            self._json(400, {"error": str(error)})
        except HTTPError:
            self._json(403, {"error": "GitHub-Zugriff auf dieses Repository fehlt"})
        except Exception:
            self._json(500, {"error": "Serverfehler bei der Anfrage"})

    def do_POST(self) -> None:
        with self._request_lock():
            self._post()

    def _post(self) -> None:
        self._audit_session = None
        try:
            try:
                session = self._session(validate=self.path != "/api/logout")
            except AccessDenied:
                raise
            except PermissionError as error:
                self._json(401, {"error": str(error)})
                return
            if self.headers.get("Origin") != self.server.config["PUBLIC_ORIGIN"].rstrip("/"):
                raise PermissionError("Ungültiger Ursprung")
            if self.headers.get("X-Editor-Token") != session["csrf"]:
                raise PermissionError("Ungültige Sitzung")
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= MAX_REQUEST or self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                raise ValueError("Ungültige Anfragegröße oder Inhaltstyp")
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict):
                raise ValueError("Ungültige Anfrage")
            store = None if self.path in {"/api/logout", "/api/repositories/select", "/api/drafts/leave"} else self._store(session)
            if self.server.access and self.path not in {"/api/logout", "/api/repositories/select", "/api/drafts/leave"}:
                role = "merge" if self.path.endswith("/merge") else "review" if self.path.startswith("/api/reviews/") else "write"
                self._require_action(session, role)
            if self.path == "/api/logout":
                with self.server.lock:
                    for sid, candidate in list(self.server.sessions.items()):
                        if candidate is session:
                            self.server.sessions.pop(sid, None)
                            break
                self._json(200, {"ok": True})
            elif self.path == "/api/repositories/select":
                repository = data.get("repository")
                if not isinstance(repository, str):
                    raise ValueError("Bitte ein Datenrepository wählen")
                self._repository(repository, session["user"], session)
                if self.server.access:
                    self.server.access.require(session, repository, force=True)
                    if repository not in self._github_repositories(session, session["token"]):
                        raise AccessDenied("Die GitHub-App ist für diesen Bestand nicht freigegeben.")
                if session["branch"] != "main":
                    raise ValueError("Bitte zuerst den geöffneten Entwurf ablegen")
                github_json("https://api.github.com/repos/" + repository, session["token"])
                owner, repo = repository.split("/")
                GitHubStore(owner, repo, session["token"]).slugs("main")
                with self.server.lock:
                    session.update(repository=repository, branch="main", purpose="case", case="")
                    session["csrf"] = secrets.token_urlsafe(32)
                self._json(200, {"repository": repository})
            elif self.path == "/api/drafts/leave":
                if session["branch"] == "main":
                    raise ValueError("Es ist kein Arbeitsentwurf geöffnet")
                session["branch"] = "main"
                session["purpose"] = "case"
                session["case"] = ""
                self._json(200, {"branch": "main", "purpose": "case"})
            elif self.path == "/api/start-branch":
                purpose = data.get("purpose", "case")
                if purpose not in ("case", "vocabulary"):
                    raise ValueError("Unbekannter Arbeitsbereich")
                case = data.get("case", "") if purpose == "case" else ""
                if purpose == "case" and case not in store.slugs("main"):
                    raise ValueError("Bitte einen Fall aus dem Datenkatalog wählen")
                if purpose == "vocabulary" and session["user"].lower() not in self._maintainers():
                    raise PermissionError("Vokabularpflege ist nur für eingetragene Ontologie-Maintainer möglich")
                if session["branch"] != "main" and session.get("purpose", "case") != purpose:
                    raise ValueError("Bitte den laufenden Arbeitszweig zuerst zur Prüfung einreichen")
                if session["branch"] != "main" and purpose == "case" and session.get("case") != case:
                    raise ValueError("Dieser Arbeitszweig gehört zu einem anderen Fall")
                if session["branch"] == "main":
                    prefix = "vocabulary" if purpose == "vocabulary" else "editor"
                    branch = f"codex/ontology-{prefix}-{session['user']}-{datetime.now(timezone.utc):%Y%m%d%H%M%S}-{secrets.token_hex(3)}"
                    store.create_branch(branch)
                    session["branch"] = branch
                    session["purpose"] = purpose
                    session["case"] = case
                self._json(200, {"branch": session["branch"], "purpose": session.get("purpose", "case"), "case": session.get("case", "")})
            elif self.path == "/api/drafts/resume":
                if session["branch"] != "main":
                    raise ValueError("Bitte den laufenden Arbeitszweig zuerst zur Prüfung einreichen")
                branch = data.get("branch", "")
                draft = next((item for item in store.list_drafts(session["user"]) if item["branch"] == branch), None)
                if draft is None:
                    raise ValueError("Dieser eigene Entwurf ist nicht mehr verfügbar")
                if draft["purpose"] == "vocabulary" and session["user"].lower() not in self._maintainers():
                    raise PermissionError("Vokabularpflege ist nur für eingetragene Ontologie-Maintainer möglich")
                if draft["purpose"] == "vocabulary":
                    store.load_vocabulary(draft["branch"])
                else:
                    case = draft["case"] or data.get("case", "")
                    if case not in store.slugs("main"):
                        raise ValueError("Bitte einen Fall aus dem Datenkatalog wählen")
                    store.load_case(case, draft["branch"])
                    draft = {**draft, "case": case}
                session["branch"] = draft["branch"]
                session["purpose"] = draft["purpose"]
                session["case"] = draft["case"]
                self._json(200, draft)
            elif self.path.startswith("/api/reviews/") and self.path.endswith("/review") and self.path.count("/") == 4:
                number = int(self.path.split("/")[3])
                author = None
                if self.server.access:
                    author = self.server.access.other_author(session, store.review_detail(number).get("author_id"))
                options = {"return_receipt": True} if self.server.access else {}
                result = store.submit_case_review(number, data.get("head_sha", ""), data.get("event", ""), data.get("body", ""), session["user"], self._notaries(), data.get("checks"), **options)
                url = result["html_url"] if self.server.access else result
                if self.server.access:
                    self.server.access.store.record_review(session["repository"], {"id": result["id"], "head": data["head_sha"],
                        "reviewer": session["principal"], "author": author, "github_id": session["user_id"], "event": data["event"]})
                self._json(200, {"url": url})
            elif self.path.startswith("/api/reviews/") and self.path.endswith("/merge") and self.path.count("/") == 4:
                if not self.server.access:
                    raise AccessDenied("Übernehmen benötigt die zentrale Benutzerverwaltung.")
                number = int(self.path.split("/")[3])
                def eligible(review, head, author_id):
                    receipt = self.server.access.store.review_receipt(session["repository"], review["id"])
                    author = self.server.access.store.principal_for_github(author_id)
                    reviewer = self.server.access.store.principal_for_github(review["user"]["id"])
                    return bool(receipt and author and reviewer and receipt["Head"] == head
                        and receipt["Event"] == "APPROVE" and receipt["Author"] == author
                        and receipt["Reviewer"] == reviewer and reviewer != author
                        and receipt["GithubId"] == str(review["user"]["id"]))
                self._json(200, store.merge_case_review(number, data.get("head_sha", ""), eligible))
            elif self.path.startswith("/api/vocabulary/") and self.path.count("/") == 3:
                if session["user"].lower() not in self._maintainers():
                    raise PermissionError("Vokabularpflege ist nur für eingetragene Ontologie-Maintainer möglich")
                if session.get("purpose") != "vocabulary" or session["branch"] == "main":
                    raise ValueError("Bitte einen Vokabular-Arbeitszweig beginnen")
                action = self.path.rsplit("/", 1)[1]
                if action == "preview":
                    self._json(200, store.preview_vocabulary(session["branch"], data))
                elif action == "save":
                    self._json(200, store.save_vocabulary(session["branch"], data))
                elif action == "review":
                    url = store.create_vocabulary_pr(session["branch"], data.get("reason", ""), data.get("source", ""))
                    session["branch"] = "main"
                    session["purpose"] = "case"
                    self._json(200, {"url": url, "branch": "main", "purpose": "case"})
                else:
                    self._json(404, {"error": "Nicht gefunden"})
            elif self.path.startswith("/api/cases/") and self.path.count("/") == 4:
                if session.get("purpose", "case") != "case":
                    raise ValueError("Für Falländerungen ist ein eigener Arbeitszweig erforderlich")
                _, _, _, slug, action = self.path.split("/")
                if action in ("preview", "save", "review") and session.get("case") != slug:
                    raise ValueError("Dieser Arbeitszweig gehört zu einem anderen Fall")
                if action == "preview":
                    self._json(200, store.preview(slug, session["branch"], data))
                elif action == "save":
                    self._json(200, store.save(slug, session["branch"], data))
                elif action == "review":
                    url = store.create_pr(slug, session["branch"], data.get("reason", ""), data.get("source", ""))
                    session["branch"] = "main"
                    session["case"] = ""
                    self._json(200, {"url": url, "branch": "main"})
                elif action == "restore-preview":
                    if session["branch"] != "main":
                        raise ValueError("Bitte die laufende Änderung zuerst zur Prüfung einreichen")
                    self._json(200, store.preview_case_restore(slug, data.get("target_sha", ""), data.get("expected_main", "")))
                elif action == "restore":
                    if session["branch"] != "main":
                        raise ValueError("Bitte die laufende Änderung zuerst zur Prüfung einreichen")
                    branch = f"codex/ontology-editor-{session['user']}-{datetime.now(timezone.utc):%Y%m%d%H%M%S}-{secrets.token_hex(3)}"
                    result = store.restore_case(slug, data.get("target_sha", ""), data.get("expected_main", ""), branch)
                    session["branch"] = branch
                    session["purpose"] = "case"
                    session["case"] = slug
                    self._json(200, result)
                else:
                    self._json(404, {"error": "Nicht gefunden"})
            else:
                self._json(404, {"error": "Nicht gefunden"})
        except AccessUnavailable as error:
            self._json(503, {"error": str(error)})
        except PermissionError as error:
            self._json(403, {"error": str(error)})
        except HTTPError as error:
            self._json(401 if error.code == 401 else 403, {"error": "GitHub-Zugriff auf dieses Repository fehlt"})
        except GitHubError as error:
            self._json(401 if error.status == 401 else 403 if error.status == 403 else 400, {"error": str(error)})
        except ValueError as error:
            self._json(400, {"error": str(error)})
        except Exception:
            self._json(500, {"error": "Serverfehler bei der Anfrage"})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8080")))
    args = parser.parse_args()
    config = require_config()
    with CloudServer((args.host, args.port), config) as server:
        print(f"NaC editor listening on port {server.server_port}")
        print(audit_line("service_started", release=release_info()["commit"]), flush=True)
        server.serve_forever()


if __name__ == "__main__":
    main()
