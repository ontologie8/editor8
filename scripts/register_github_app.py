# SPDX-License-Identifier: AGPL-3.0-or-later
"""Register the private editor GitHub App via GitHub's browser manifest flow.

The one-time registration code and generated credentials stay in this process.
Credentials are written directly to Azure Key Vault, never to Git or stdout.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import secrets
import shutil
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse


def manifest(origin: str, redirect_url: str) -> dict:
    return {
        "name": "NaC Ontology Editor notariat8",
        "url": origin,
        "description": "GitOps editor for the 20 NaC notarial case ontologies",
        "redirect_url": redirect_url,
        "callback_urls": [origin + "/callback"],
        "hook_attributes": {"url": origin + "/github-webhook", "active": False},
        "public": False,
        "default_events": [],
        "default_permissions": {"contents": "write", "pull_requests": "write"},
        "request_oauth_on_install": False,
    }


def run_az(*args: str) -> None:
    az_executable = shutil.which("az.cmd" if os.name == "nt" else "az")
    if not az_executable:
        raise RuntimeError("Azure CLI nicht gefunden")
    command = [az_executable, *args, "--only-show-errors", "--output", "none"]
    for attempt in range(5):
        result = subprocess.run(command, capture_output=True, text=True, timeout=120, check=False)
        if result.returncode == 0:
            return
        if attempt < 4:
            time.sleep(5 * (attempt + 1))
    raise RuntimeError("Azure-Vorgang fehlgeschlagen: " + " ".join(args[:3]))


def put_secret(vault: str, name: str, value: str) -> None:
    path = ""
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="", delete=False) as secret_file:
            path = secret_file.name
            secret_file.write(value)
        run_az(
            "keyvault", "secret", "set",
            "--vault-name", vault,
            "--name", name,
            "--file", path,
            "--encoding", "utf-8",
        )
    finally:
        if path and os.path.exists(path):
            os.unlink(path)


def exchange_manifest_code(code: str) -> dict:
    request = urllib.request.Request(
        "https://api.github.com/app-manifests/" + code + "/conversions",
        data=b"",
        method="POST",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "nac-ontology-editor-bootstrap"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def register(args: argparse.Namespace) -> None:
    origin = args.origin.rstrip("/")
    parsed = urlparse(origin)
    if parsed.scheme != "https" or not parsed.netloc or parsed.path or parsed.query or parsed.fragment:
        raise ValueError("--origin muss ein HTTPS-Ursprung ohne Pfad sein")
    if args.org != "notariat8" or args.repo != "ontology":
        raise ValueError("Dieses Bootstrap-Skript ist auf notariat8/ontology begrenzt")
    server = HTTPServer(("127.0.0.1", 0), BaseHTTPRequestHandler)
    state = secrets.token_urlsafe(32)
    redirect_url = "http://127.0.0.1:" + str(server.server_port) + "/complete/" + state
    app_manifest = manifest(origin, redirect_url)
    registration_url = "https://github.com/organizations/notariat8/settings/apps/new"
    result: dict[str, str] = {}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, _format: str, *_values: object) -> None:
            # The callback URL contains a one-time code.
            return

        def send_page(self, status: int, body: str) -> None:
            data = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'none'; form-action https://github.com; style-src 'unsafe-inline'",
            )
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self) -> None:
            url = urlparse(self.path)
            if url.path == "/":
                content = html.escape(json.dumps(app_manifest, ensure_ascii=False), quote=True)
                page = (
                    "<!doctype html><html lang='de'><meta charset='utf-8'>"
                    "<title>NaC Editor: GitHub App</title>"
                    "<style>body{font:18px system-ui;max-width:42rem;margin:3rem auto;line-height:1.5}"
                    "button{font:inherit;padding:.7rem 1rem}</style>"
                    "<h1>GitHub App für den NaC Editor</h1>"
                    "<p>Der folgende Schritt legt die App in der Organisation notariat8 an."
                    "GitHub zeigt die Rechte vor der Bestätigung an: Inhalte und Pull Requests"
                    " lesen und schreiben. Nachher wird die App nur auf das Repository"
                    " notariat8/ontology installiert.</p>"
                    "<form method='post' action='" + registration_url + "'>"
                    "<input type='hidden' name='manifest' value='" + content + "'>"
                    "<input type='hidden' name='state' value='" + html.escape(state, quote=True) + "'>"
                    "<button type='submit'>Auf GitHub prüfen und anlegen</button></form></html>"
                )
                self.send_page(200, page)
                return
            if url.path != "/complete/" + state:
                self.send_page(404, "<h1>Nicht gefunden</h1>")
                return
            query = parse_qs(url.query)
            if query.get("state") != [state] or len(query.get("code", [])) != 1:
                self.send_page(400, "<h1>Ungültige GitHub-Rückgabe</h1>")
                return
            code = query["code"][0]
            try:
                app = exchange_manifest_code(code)
                if app.get("owner", {}).get("login", "").lower() != args.org:
                    raise RuntimeError("GitHub-App gehört nicht zur erwarteten Organisation")
                if not all(app.get(key) for key in ("client_id", "client_secret", "pem", "slug")):
                    raise RuntimeError("GitHub lieferte unvollständige App-Daten")
                result.update(slug=app["slug"], client_id=app["client_id"])
                put_secret(args.vault, "github-app-client-secret", app["client_secret"])
                put_secret(args.vault, "github-app-private-key", app["pem"])
                if app.get("webhook_secret"):
                    put_secret(args.vault, "github-app-webhook-secret", app["webhook_secret"])
                run_az(
                    "containerapp", "secret", "set",
                    "--resource-group", args.resource_group,
                    "--name", args.container_app,
                    "--secrets",
                    "github-client-secret=keyvaultref:"
                    + "https://" + args.vault + ".vault.azure.net/secrets/github-app-client-secret"
                    + ",identityref:system",
                )
                run_az(
                    "containerapp", "update",
                    "--resource-group", args.resource_group,
                    "--name", args.container_app,
                    "--set-env-vars", "GITHUB_APP_CLIENT_ID=" + app["client_id"],
                )
                install_url = "https://github.com/apps/" + app["slug"] + "/installations/new"
                self.send_page(
                    200,
                    "<!doctype html><html lang='de'><meta charset='utf-8'>"
                    "<h1>GitHub App eingerichtet</h1>"
                    "<p>Die Zugangsdaten sind im Azure Key Vault gespeichert."
                    " Installiere die App jetzt in notariat8 und wähle dort"
                    " <strong>nur notariat8/ontology</strong>.</p>"
                    "<p><a href='" + html.escape(install_url, quote=True)
                    + "'>GitHub App gezielt installieren</a></p></html>",
                )
            except Exception as error:
                result["error"] = type(error).__name__
                self.send_page(
                    500,
                    "<!doctype html><html lang='de'><meta charset='utf-8'>"
                    "<h1>Einrichtung nicht abgeschlossen</h1>"
                    "<p>Die Zugangsdaten wurden nicht im Chat ausgegeben."
                    " Den Fehler bitte im Codex-Terminal prüfen.</p></html>",
                )

    server.RequestHandlerClass = Handler
    server.timeout = 1
    local_url = "http://127.0.0.1:" + str(server.server_port) + "/"
    print("LOKALE_GITHUB_REGISTRIERUNG=" + local_url, flush=True)
    webbrowser.open(local_url)
    deadline = time.monotonic() + args.timeout
    while time.monotonic() < deadline and not result:
        server.handle_request()
    server.server_close()
    if "error" in result:
        if "slug" in result:
            print("APP_SLUG=" + result["slug"])
            print("CLIENT_ID=" + result["client_id"])
        raise RuntimeError("GitHub-App-Einrichtung fehlgeschlagen: " + result["error"])
    if not result:
        raise TimeoutError("GitHub-App-Registrierung nicht innerhalb des Zeitfensters abgeschlossen")
    print("APP_SLUG=" + result["slug"])
    print("CLIENT_ID=" + result["client_id"])
    print("INSTALLATION_URL=https://github.com/apps/" + result["slug"] + "/installations/new")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origin", required=True)
    parser.add_argument("--org", default="notariat8")
    parser.add_argument("--repo", default="ontology")
    parser.add_argument("--vault", required=True)
    parser.add_argument("--resource-group", required=True)
    parser.add_argument("--container-app", required=True)
    parser.add_argument("--timeout", type=int, default=600)
    register(parser.parse_args())


if __name__ == "__main__":
    main()
