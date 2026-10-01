# SPDX-License-Identifier: AGPL-3.0-or-later
"""Single-instance hosted NaC editor with GitHub App user authentication.

Required environment: GITHUB_APP_CLIENT_ID, GITHUB_APP_CLIENT_SECRET,
GITHUB_REPOSITORY (owner/repo), PUBLIC_ORIGIN (https://editor.example.org),
EDITOR_USERS (comma-separated GitHub usernames).
TLS terminates at the trusted hosting proxy. Sessions are kept in memory and
expire after eight hours; a restart signs editors out without losing Git data.
"""

from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import secrets
import threading
import time
from urllib.error import HTTPError
from urllib.parse import parse_qs, quote, urlencode, urlparse
from urllib.request import Request, urlopen

from rdflib import Graph, Namespace
from rdflib.namespace import SKOS

from data_contract import APP_ROOT
from github_store import GitHubError, GitHubStore


ASSETS = APP_ROOT / "editor"
MAX_REQUEST = 250_000
SESSION_LIFETIME = 8 * 60 * 60
AUTH_LIFETIME = 5 * 60


def require_config() -> dict[str, str]:
    names = ("GITHUB_APP_CLIENT_ID", "GITHUB_APP_CLIENT_SECRET", "GITHUB_REPOSITORY", "PUBLIC_ORIGIN", "EDITOR_USERS")
    config = {name: os.environ.get(name, "") for name in names}
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
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self'; script-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'")
        for key, value in (extra or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: int, payload: dict | list) -> None:
        self._send(status, json.dumps(payload, ensure_ascii=False).encode("utf-8"), "application/json")

    def _redirect(self, target: str, cookies: list[str] | None = None) -> None:
        self.send_response(302)
        self.send_header("Location", target)
        self.send_header("Cache-Control", "no-store")
        for cookie in cookies or []:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()

    def _session(self) -> dict:
        jar = SimpleCookie()
        try:
            jar.load(self.headers.get("Cookie", ""))
            sid = jar["nac_session"].value if "nac_session" in jar else ""
        except Exception:
            sid = ""
        with self.server.lock:
            session = self.server.sessions.get(sid)
            if session and time.time() - session["created"] < SESSION_LIFETIME:
                return session
            self.server.sessions.pop(sid, None)
        raise PermissionError("Bitte bei GitHub anmelden")

    def _store(self, session: dict) -> GitHubStore:
        return GitHubStore(self.server.owner, self.server.repo, session["token"])

    def _notaries(self) -> set[str]:
        return {name.strip().lower() for name in self.server.config.get("NOTARY_REVIEWERS", "").split(",") if name.strip()}

    def _maintainers(self) -> set[str]:
        return {name.strip().lower() for name in self.server.config.get("ONTOLOGY_MAINTAINERS", "").split(",") if name.strip()}

    def _login(self) -> None:
        state = secrets.token_urlsafe(24)
        verifier = secrets.token_urlsafe(48)
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
        with self.server.lock:
            now = time.time()
            self.server.pending = {key: value for key, value in self.server.pending.items() if now - value["created"] < AUTH_LIFETIME}
            self.server.sessions = {key: value for key, value in self.server.sessions.items() if now - value["created"] < SESSION_LIFETIME}
            if len(self.server.pending) >= 100:
                raise ValueError("Zu viele laufende Anmeldungen. Bitte später erneut versuchen.")
            self.server.pending[state] = {"verifier": verifier, "created": time.time()}
        params = {
            "client_id": self.server.config["GITHUB_APP_CLIENT_ID"],
            "redirect_uri": self.server.config["PUBLIC_ORIGIN"].rstrip("/") + "/callback",
            "state": state, "code_challenge": challenge, "code_challenge_method": "S256",
        }
        self._redirect("https://github.com/login/oauth/authorize?" + urlencode(params), [
            f"nac_oauth_state={state}; Path=/callback; Max-Age={AUTH_LIFETIME}; HttpOnly; Secure; SameSite=Lax"
        ])

    def _callback(self, query: dict[str, list[str]]) -> None:
        state = query.get("state", [""])[0]
        code = query.get("code", [""])[0]
        jar = SimpleCookie()
        jar.load(self.headers.get("Cookie", ""))
        if not state or "nac_oauth_state" not in jar or jar["nac_oauth_state"].value != state:
            raise PermissionError("Anmeldung stimmt nicht mit diesem Browser überein")
        with self.server.lock:
            pending = self.server.pending.pop(state, None)
        if not pending or time.time() - pending["created"] > AUTH_LIFETIME or not code:
            raise PermissionError("Anmeldung abgelaufen. Bitte erneut beginnen.")
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
            raise PermissionError("GitHub-Anmeldung fehlgeschlagen")
        user = github_json("https://api.github.com/user", token)
        allowed = {name.strip().lower() for name in self.server.config["EDITOR_USERS"].split(",")}
        if user["login"].lower() not in allowed:
            raise PermissionError("Dieses GitHub-Konto ist nicht als Editor freigeschaltet")
        # A readable repo and a working user token are required; write permission
        # is enforced again by GitHub when creating branches or commits.
        github_json(f"https://api.github.com/repos/{self.server.owner}/{self.server.repo}", token)
        sid = secrets.token_urlsafe(32)
        with self.server.lock:
            self.server.sessions[sid] = {
                "token": token, "user": user["login"], "csrf": secrets.token_urlsafe(32),
                "branch": "main", "created": time.time(),
            }
        self._redirect("/", [
            f"nac_session={sid}; Path=/; Max-Age={SESSION_LIFETIME}; HttpOnly; Secure; SameSite=Lax",
            "nac_oauth_state=; Path=/callback; Max-Age=0; HttpOnly; Secure; SameSite=Lax",
        ])

    def _catalog(self, catalog_text: str, case_ids: list[str]) -> list[dict]:
        graph = Graph().parse(data=catalog_text, format="turtle")
        n8 = Namespace("https://notariat8.github.io/ontology/id/")
        return [{"slug": slug, "title": str(graph.value(n8[f"vorgangsart-{slug}"], SKOS.prefLabel))} for slug in case_ids]

    def do_GET(self) -> None:
        try:
            path = urlparse(self.path)
            if path.path == "/healthz":
                self._json(200, {"status": "ok"})
            elif path.path == "/login":
                self._login()
            elif path.path == "/callback":
                self._callback(parse_qs(path.query))
            elif path.path in ("/", "/index.html", "/app.js", "/style.css"):
                filename = "index.html" if path.path == "/" else path.path.lstrip("/")
                kind = {"index.html": "text/html", "app.js": "text/javascript", "style.css": "text/css"}
                self._send(200, (ASSETS / filename).read_bytes(), kind[filename])
            elif path.path == "/api/status":
                session = self._session()
                self._json(200, {"token": session["csrf"], "branch": session["branch"], "purpose": session.get("purpose", "case"), "case": session.get("case", ""), "hosted": True, "user": session["user"], "notary_reviewer": session["user"].lower() in self._notaries(), "ontology_maintainer": session["user"].lower() in self._maintainers()})
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
                if cached and cached[0] == main_ref:
                    index = cached[1]
                else:
                    index = store.case_index(main_ref)
                    with self.server.lock:
                        self.server.case_index_cache = (main_ref, index)
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
                if cached and cached[0] == main_ref:
                    impact = cached[1]
                else:
                    impact = store.vocabulary_impact(main_ref)
                    with self.server.lock:
                        self.server.impact_cache = (main_ref, impact)
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
        try:
            try:
                session = self._session()
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
            store = self._store(session)
            if self.path == "/api/logout":
                with self.server.lock:
                    for sid, candidate in list(self.server.sessions.items()):
                        if candidate is session:
                            self.server.sessions.pop(sid, None)
                            break
                self._json(200, {"ok": True})
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
                url = store.submit_case_review(number, data.get("head_sha", ""), data.get("event", ""), data.get("body", ""), session["user"], self._notaries(), data.get("checks"))
                self._json(200, {"url": url})
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
        except PermissionError as error:
            self._json(403, {"error": str(error)})
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
        server.serve_forever()


if __name__ == "__main__":
    main()
