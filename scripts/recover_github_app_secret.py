# SPDX-License-Identifier: AGPL-3.0-or-later
"""Receive a newly generated GitHub App client secret in a local browser form.

This is only for recovery after manifest registration completed but credential
storage failed. The secret is sent to Azure Key Vault without chat or Git.
"""

from __future__ import annotations

import argparse
import html
import secrets
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs

from register_github_app import put_secret, run_az


def recover(args: argparse.Namespace) -> None:
    if args.client_id != "Iv23liPjhZBeInpKOJOr":
        raise ValueError("Unerwartete GitHub-App-Client-ID")
    server = HTTPServer(("127.0.0.1", 0), BaseHTTPRequestHandler)
    token = secrets.token_urlsafe(32)
    result: dict[str, str] = {}
    settings_url = "https://github.com/organizations/notariat8/settings/apps"

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, _format: str, *_values: object) -> None:
            return

        def page(self, status: int, body: str) -> None:
            data = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'none'; form-action 'self'; style-src 'unsafe-inline'",
            )
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self) -> None:
            if self.path != "/":
                self.page(404, "<h1>Nicht gefunden</h1>")
                return
            body = (
                "<!doctype html><html lang='de'><meta charset='utf-8'>"
                "<title>NaC GitHub App verbinden</title>"
                "<style>body{font:18px system-ui;max-width:42rem;margin:3rem auto;line-height:1.5}"
                "input{font:inherit;width:100%;padding:.5rem}button{font:inherit;padding:.7rem 1rem}</style>"
                "<h1>GitHub App verbinden</h1>"
                "<p>Öffne die <a href='" + settings_url + "' target='_blank' rel='noreferrer'>"
                "GitHub-App-Einstellungen</a>, bearbeite"
                " <strong>NaC Ontology Editor notariat8</strong> und wähle"
                " <strong>Generate a new client secret</strong>.</p>"
                "<p>Füge das neue Secret ausschließlich hier ein. Diese Seite läuft nur auf"
                " 127.0.0.1; sie schreibt das Secret direkt in Azure Key Vault."
                " Nach erfolgreichem Speichern entferne das ältere, verlorene Secret"
                " in den GitHub-App-Einstellungen.</p>"
                "<form method='post' action='/submit/" + html.escape(token, quote=True) + "'>"
                "<label>Neues Client-Secret<input type='password' name='client_secret'"
                " autocomplete='off' required></label>"
                "<p><button type='submit'>Sicher in Azure speichern</button></p></form></html>"
            )
            self.page(200, body)

        def do_POST(self) -> None:
            if self.path != "/submit/" + token:
                self.page(404, "<h1>Nicht gefunden</h1>")
                return
            if self.headers.get("Content-Type", "").split(";")[0] != "application/x-www-form-urlencoded":
                self.page(415, "<h1>Ungültige Eingabe</h1>")
                return
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 4096:
                self.page(400, "<h1>Ungültige Eingabelänge</h1>")
                return
            values = parse_qs(self.rfile.read(length).decode("utf-8"), strict_parsing=True)
            submitted = values.get("client_secret", [])
            if len(submitted) != 1 or not (20 <= len(submitted[0]) <= 256):
                self.page(400, "<h1>Ungültiges Secret-Format</h1>")
                return
            try:
                put_secret(args.vault, "github-app-client-secret", submitted[0])
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
                    "--set-env-vars", "GITHUB_APP_CLIENT_ID=" + args.client_id,
                )
                result["status"] = "stored"
                self.page(
                    200,
                    "<!doctype html><html lang='de'><meta charset='utf-8'>"
                    "<h1>Azure-Verbindung eingerichtet</h1>"
                    "<p>Das neue Secret liegt im Key Vault. Entferne das ältere,"
                    " verlorene Secret in GitHub und installiere die App nur"
                    " auf notariat8/ontology.</p></html>",
                )
            except Exception as error:
                result["status"] = "failed"
                result["error"] = type(error).__name__
                self.page(
                    500,
                    "<!doctype html><html lang='de'><meta charset='utf-8'>"
                    "<h1>Azure-Verbindung fehlgeschlagen</h1>"
                    "<p>Das Secret wurde nicht im Chat ausgegeben.</p></html>",
                )

    server.RequestHandlerClass = Handler
    server.timeout = 1
    local_url = "http://127.0.0.1:" + str(server.server_port) + "/"
    print("LOKALE_SECRET_EINGABE=" + local_url, flush=True)
    webbrowser.open(local_url)
    deadline = time.monotonic() + args.timeout
    while time.monotonic() < deadline and not result:
        server.handle_request()
    server.server_close()
    if not result:
        raise TimeoutError("Eingabezeitfenster abgelaufen")
    if result["status"] != "stored":
        raise RuntimeError("Azure-Verbindung fehlgeschlagen: " + result.get("error", "unbekannt"))
    print("GITHUB_APP_SECRET_IN_KEY_VAULT=true")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vault", required=True)
    parser.add_argument("--resource-group", required=True)
    parser.add_argument("--container-app", required=True)
    parser.add_argument("--client-id", required=True)
    parser.add_argument("--timeout", type=int, default=900)
    recover(parser.parse_args())


if __name__ == "__main__":
    main()
