# SPDX-License-Identifier: AGPL-3.0-or-later
"""Local browser editor for the 20 NaC cases and their shared vocabulary.

Run: python scripts/case_editor.py
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
from urllib.parse import urlparse
import webbrowser

from rdflib import Graph

from case_editor_model import APP_ROOT, ROOT, case_path, load_case, prepare_change, revision, slugs, validate_model
from case_restore import prepare_historical_case
from case_index import build_case_index
from vocabulary_editor import model as vocabulary_model, prepare_change as prepare_vocabulary_change
from vocabulary_impact import impact_index
from release_info import release_info
from brand_assets import BRAND_ASSETS
from learning_assets import LEARNING_ASSETS


ASSETS = APP_ROOT / "editor"
MAX_REQUEST = 250_000
EDITOR_BRANCH = re.compile(r"codex/ontology-editor-[0-9]{8}-[0-9]{6}$")
VOCABULARY_BRANCH = re.compile(r"codex/ontology-vocabulary-[0-9]{8}-[0-9]{6}$")


def git_branch() -> str:
    return subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip()


def start_branch(purpose: str = "case") -> str:
    if purpose not in ("case", "vocabulary"):
        raise ValueError("Unbekannter Arbeitsbereich")
    current = git_branch()
    if current != "main":
        if purpose == "vocabulary" and not VOCABULARY_BRANCH.fullmatch(current):
            raise ValueError("Bitte die laufende Falländerung zuerst zur Prüfung einreichen")
        if purpose == "case" and VOCABULARY_BRANCH.fullmatch(current):
            raise ValueError("Bitte die laufende Vokabularänderung zuerst zur Prüfung einreichen")
        return current
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    branch = f"codex/ontology-{'vocabulary' if purpose == 'vocabulary' else 'editor'}-{stamp}"
    subprocess.run(["git", "switch", "-c", branch], cwd=ROOT, check=True, capture_output=True, text=True)
    return branch


def local_case_history(slug: str) -> dict:
    case_path(slug)
    main_ref = subprocess.check_output(["git", "rev-parse", "main"], cwd=ROOT, text=True).strip()
    path = f"cases/{slug}/ontology.ttl"
    output = subprocess.check_output(["git", "log", "-n", "20", "main", "--format=%H%x1f%an%x1f%aI%x1f%s", "--", path], cwd=ROOT, text=True)
    entries = []
    for line in output.splitlines():
        sha, author, date, message = line.split("\x1f", 3)
        entries.append({"sha": sha, "author": author, "date": date, "message": message, "url": f"https://github.com/notariat8/ontology/commit/{sha}"})
    return {"main_ref": main_ref, "case": slug, "entries": entries}


def preview_local_case_restore(slug: str, data: dict) -> tuple[dict, dict]:
    if git_branch() != "main":
        raise ValueError("Bitte die laufende Änderung zuerst zur Prüfung einreichen")
    history = local_case_history(slug)
    if data.get("expected_main") != history["main_ref"]:
        raise ValueError("Der Katalog wurde inzwischen geändert. Fall und Historie neu laden.")
    target = data.get("target_sha", "")
    if target not in {item["sha"] for item in history["entries"]}:
        raise ValueError("Die frühere Fassung ist nicht in der angezeigten Fallhistorie")
    historical = subprocess.check_output(["git", "show", f"{target}:cases/{slug}/ontology.ttl"], cwd=ROOT).decode("utf-8")
    proposal = prepare_historical_case(slug, historical, ROOT, describe_changes)
    return history, proposal


def restore_local_case(slug: str, data: dict) -> dict:
    history, proposal = preview_local_case_restore(slug, data)
    if not proposal["changed"]:
        raise ValueError("Die frühere Fassung entspricht bereits dem aktuellen Fall")
    branch = start_branch("case")
    result = write_change(slug, proposal["model"])
    return {"branch": branch, "expected_ref": history["main_ref"], "changed": result["changed"], "changes": proposal["changes"]}


def write_change(slug: str, data: dict) -> dict:
    path = case_path(slug)
    if git_branch() == "main":
        raise ValueError("Bitte zuerst mit „Änderung beginnen“ einen Arbeitszweig anlegen.")
    if VOCABULARY_BRANCH.fullmatch(git_branch()):
        raise ValueError("Falländerungen und gemeinsames Vokabular brauchen getrennte Arbeitszweige")
    ttl, page, changed = prepare_change(slug, data, data.get("revision", ""))
    if not changed:
        return {"changed": False, "revision": revision(path)}
    page_path = path.with_name("README.md")
    # Render and parse before either maintained file is replaced.
    Graph().parse(data=ttl, format="turtle")
    old_ttl = path.read_bytes()
    old_page = page_path.read_bytes()
    temp_files: list[Path] = []
    try:
        for target, content in ((path, ttl), (page_path, page)):
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", newline="\n", dir=target.parent,
                prefix=".case-editor-", suffix=".tmp", delete=False,
            ) as handle:
                handle.write(content)
                temp_files.append(Path(handle.name))
        temp_files[0].replace(path)
        temp_files[1].replace(page_path)
    except Exception:
        # Restore both files if the second replacement fails.
        path.write_bytes(old_ttl)
        page_path.write_bytes(old_page)
        raise
    finally:
        for temporary in temp_files:
            temporary.unlink(missing_ok=True)
    return {"changed": True, "revision": revision(path)}


def write_vocabulary_change(data: dict) -> dict:
    if not VOCABULARY_BRANCH.fullmatch(git_branch()):
        raise ValueError("Für das Vokabular ist ein eigener Arbeitszweig erforderlich")
    path = ROOT / "ontology/core.ttl"
    original = path.read_text(encoding="utf-8")
    ttl, _, changed = prepare_vocabulary_change(original, data)
    if changed:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=path.parent, prefix=".vocabulary-editor-", suffix=".tmp", delete=False) as handle:
            handle.write(ttl)
            temporary = Path(handle.name)
        try:
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)
    return {"changed": changed, "revision": revision(path)}


def submit_vocabulary_review(data: dict) -> dict:
    branch = git_branch()
    if not VOCABULARY_BRANCH.fullmatch(branch):
        raise ValueError("Bitte zuerst einen Vokabular-Arbeitszweig beginnen")
    reason, source = data.get("reason"), data.get("source")
    if not isinstance(reason, str) or not 15 <= len(reason.strip()) <= 3000 or not isinstance(source, str) or not 5 <= len(source.strip()) <= 1000:
        raise ValueError("Fachlicher Grund und Quellenstand fehlen")
    expected = {"ontology/core.ttl"}
    pending = set(subprocess.check_output(["git", "diff", "--name-only", "HEAD"], cwd=ROOT, text=True).splitlines())
    existing = set(subprocess.check_output(["git", "diff", "--name-only", "main...HEAD"], cwd=ROOT, text=True).splitlines())
    if pending - expected or existing - expected or not (pending or existing):
        raise ValueError("Der Arbeitszweig enthält keine passende oder weitere Änderungen")
    if pending:
        for script, args in (("validate_catalog.py", []), ("validate_cases.py", []), ("render_case_docs.py", ["--check"])):
            subprocess.run([sys.executable, str(ROOT / "scripts" / script), *args], cwd=ROOT, check=True, capture_output=True, text=True)
        subprocess.run(["git", "add", "--", "ontology/core.ttl"], cwd=ROOT, check=True, capture_output=True, text=True)
        subprocess.run(["git", "commit", "-m", "Propose shared ontology vocabulary change"], cwd=ROOT, check=True, capture_output=True, text=True)
        subprocess.run(["git", "push", "-u", "origin", branch], cwd=ROOT, check=True, capture_output=True, text=True)
    try:
        url = subprocess.check_output(["gh", "pr", "view", branch, "--json", "url", "--jq", ".url"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
        if url.startswith("https://github.com/"):
            return {"url": url, "branch": branch, "purpose": "vocabulary"}
    except subprocess.CalledProcessError:
        pass
    body = f"## Fachlicher Grund\n\n{reason.strip()}\n\n## Quellenstand\n\n{source.strip()}\n\n## Freigabe\n\nNotarielle Fachprüfung ausstehend.\n"
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".md", delete=False) as handle:
        handle.write(body)
        body_file = Path(handle.name)
    try:
        url = subprocess.check_output(["gh", "pr", "create", "--base", "main", "--head", branch, "--title", "Fachliche Änderung: gemeinsames Vokabular", "--body-file", str(body_file)], cwd=ROOT, text=True).strip()
    finally:
        body_file.unlink(missing_ok=True)
    if not url.startswith("https://github.com/"):
        raise ValueError("Pull Request wurde erstellt, aber seine Adresse konnte nicht gelesen werden")
    return {"url": url, "branch": branch, "purpose": "vocabulary"}


def describe_changes(current: dict, proposed: dict) -> list[str]:
    """Explain two case models in terms a reviewer can inspect."""
    relation_labels = {
        "erfordert": "erfordert", "informiert": "informiert",
        "blockiertBisVollstaendig": "wartet auf vollständige Angaben",
        "blockiertBisGeprueft": "wartet auf Prüfung",
        "erfordertEntscheidung": "erfordert Entscheidung",
        "belegtDurch": "belegt durch", "fuellt": "füllt", "bestimmt": "bestimmt",
    }
    before = {node["id"]: node for node in current["nodes"]}
    after = {node["id"]: node for node in proposed["nodes"]}
    labels = {"label": "Bezeichnung", "category": "Art", "status": "Status", "question": "Fachfrage", "section": "Kapitel", "detail": "Erläuterung", "owner_role": "Rolle", "privacy_class": "Datenschutzklasse", "required_for": "Benötigt für", "options": "Optionen", "document_source": "Dokumentquelle", "contains_personal_data": "Personendaten-Hinweis"}
    def display(value: object) -> str:
        if value is None or value == "" or value == []:
            return "(leer)"
        if value is True:
            return "Ja"
        if value is False:
            return "Nein"
        if isinstance(value, list):
            return ", ".join(map(str, value))
        return str(value)

    changes = []
    if current["summary"] != proposed["summary"]:
        changes.append(f"Kurzbeschreibung: {display(current['summary'])} → {display(proposed['summary'])}")
    if current["sources"] != proposed["sources"]:
        changes.append(f"Rechtsquellen: {display(current['sources'])} → {display(proposed['sources'])}")
    for node_id in sorted(after.keys() - before.keys()):
        changes.append(f"Baustein hinzugefügt: {after[node_id]['label']}")
    for node_id in sorted(before.keys() - after.keys()):
        changes.append(f"Baustein entfernt: {before[node_id]['label']}")
    for node_id in sorted(before.keys() & after.keys()):
        fields = [key for key in after[node_id] if key != "id" and before[node_id].get(key) != after[node_id][key]]
        for field in fields:
            changes.append(f"{after[node_id]['label']} · {labels.get(field, field)}: {display(before[node_id].get(field))} → {display(after[node_id][field])}")
    old_edges = {(edge["from"], edge["type"], edge["to"]) for edge in current["edges"]}
    new_edges = {(edge["from"], edge["type"], edge["to"]) for edge in proposed["edges"]}
    for source, relation, target in sorted(new_edges - old_edges):
        changes.append(f"Beziehung hinzugefügt: {after[source]['label']} → {relation_labels[relation]} → {after[target]['label']}")
    for source, relation, target in sorted(old_edges - new_edges):
        changes.append(f"Beziehung entfernt: {before[source]['label']} → {relation_labels[relation]} → {before[target]['label']}")
    return changes


def preview_change(slug: str, data: dict, root: Path | None = None) -> dict:
    """Describe an edit in domain terms after the same validation used by save."""
    current = load_case(slug, root)
    _, _, semantic_change = prepare_change(slug, data, data.get("revision", ""), root)
    proposed = validate_model(slug, data, root)
    return {"changed": semantic_change, "changes": describe_changes(current, proposed) if semantic_change else [], "case": current["title"]}


def submit_review(slug: str, data: dict) -> dict:
    """Publish exactly one edited case as a PR for notarial review."""
    case_path(slug)
    branch = git_branch()
    if not EDITOR_BRANCH.fullmatch(branch):
        raise ValueError("Bitte eine neue Änderung über „Änderung beginnen“ anlegen.")
    reason = data.get("reason", "")
    source = data.get("source", "")
    if not isinstance(reason, str) or not 15 <= len(reason.strip()) <= 3000:
        raise ValueError("Bitte den fachlichen Grund in mindestens 15 Zeichen beschreiben.")
    if not isinstance(source, str) or not 5 <= len(source.strip()) <= 1000:
        raise ValueError("Bitte den verwendeten Quellenstand angeben.")
    expected = {f"cases/{slug}/ontology.ttl", f"cases/{slug}/README.md"}
    pending = set(subprocess.check_output(["git", "diff", "--name-only", "HEAD"], cwd=ROOT, text=True).splitlines())
    if pending and pending != expected:
        raise ValueError("Auf diesem Arbeitszweig liegen weitere oder unvollständige Änderungen. Bitte separat prüfen.")
    existing = set(subprocess.check_output(["git", "diff", "--name-only", "main...HEAD"], cwd=ROOT, text=True).splitlines())
    if existing and (existing != expected or pending):
        raise ValueError("Dieser Arbeitszweig enthält bereits andere Änderungen. Bitte separat prüfen.")
    if not pending and not existing:
        raise ValueError("Keine gespeicherte Änderung vorhanden.")
    if pending:
        for script, args in (("validate_catalog.py", []), ("validate_cases.py", []), ("render_case_docs.py", ["--check"])):
            subprocess.run([sys.executable, str(ROOT / "scripts" / script), *args], cwd=ROOT, check=True, capture_output=True, text=True)
        subprocess.run(["git", "add", "--", *sorted(expected)], cwd=ROOT, check=True, capture_output=True, text=True)
        subprocess.run(["git", "commit", "-m", f"Propose ontology change for {slug}"], cwd=ROOT, check=True, capture_output=True, text=True)
        subprocess.run(["git", "push", "-u", "origin", branch], cwd=ROOT, check=True, capture_output=True, text=True)
    try:
        existing_url = subprocess.check_output(["gh", "pr", "view", branch, "--json", "url", "--jq", ".url"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
        if existing_url.startswith("https://github.com/"):
            return {"url": existing_url}
    except subprocess.CalledProcessError:
        pass
    title = f"Fachliche Änderung: {load_case(slug)['title']}"
    body = f"## Fachlicher Grund\n\n{reason.strip()}\n\n## Quellenstand\n\n{source.strip()}\n\n## Prüfung\n\nTurtle, Fallgraph und Mermaid technisch geprüft. Notarielle Fachfreigabe steht aus.\n"
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".md", delete=False) as handle:
        handle.write(body)
        body_file = Path(handle.name)
    try:
        url = subprocess.check_output(["gh", "pr", "create", "--base", "main", "--head", branch, "--title", title, "--body-file", str(body_file)], cwd=ROOT, text=True).strip()
    finally:
        body_file.unlink(missing_ok=True)
    if not url.startswith("https://github.com/"):
        raise ValueError("Pull Request wurde erstellt, aber seine Adresse konnte nicht gelesen werden.")
    return {"url": url}


class EditorServer(ThreadingHTTPServer):
    def __init__(self, address: tuple[str, int]):
        super().__init__(address, EditorHandler)
        self.token = secrets.token_urlsafe(32)


class EditorHandler(BaseHTTPRequestHandler):
    server: EditorServer

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self'; script-src 'self'; base-uri 'none'; form-action 'none'")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: int, payload: dict | list) -> None:
        self._send(status, json.dumps(payload, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def do_GET(self) -> None:
        try:
            path = urlparse(self.path).path
            if path == "/api/release":
                self._json(200, release_info())
            elif path == "/api/status":
                branch = git_branch()
                self._json(200, {"token": self.server.token, "branch": branch, "purpose": "vocabulary" if VOCABULARY_BRANCH.fullmatch(branch) else "case", "ontology_maintainer": True})
            elif path == "/api/cases":
                from rdflib import Namespace
                from rdflib.namespace import SKOS
                catalog = Graph().parse(ROOT / "catalog/nac-usecases.ttl", format="turtle")
                n8 = Namespace("https://notariat8.github.io/ontology/id/")
                self._json(200, [{"slug": slug, "title": str(catalog.value(n8[f"vorgangsart-{slug}"], SKOS.prefLabel))} for slug in slugs()])
            elif path == "/api/case-index":
                read = lambda relative: (ROOT / relative).read_text(encoding="utf-8")
                self._json(200, build_case_index(read("catalog/nac-usecases.ttl"), {slug: read(f"cases/{slug}/ontology.ttl") for slug in slugs()}, "lokaler Arbeitsstand"))
            elif path.startswith("/api/cases/") and path.count("/") == 3:
                self._json(200, load_case(path.rsplit("/", 1)[1]))
            elif path.startswith("/api/cases/") and path.endswith("/turtle") and path.count("/") == 4:
                slug = path.split("/")[3]
                self._json(200, {"turtle": case_path(slug).read_text(encoding="utf-8")})
            elif path.startswith("/api/cases/") and path.endswith("/history") and path.count("/") == 4:
                self._json(200, local_case_history(path.split("/")[3]))
            elif path == "/api/vocabulary":
                self._json(200, vocabulary_model((ROOT / "ontology/core.ttl").read_text(encoding="utf-8")))
            elif path == "/api/drafts":
                self._json(200, [])
            elif path == "/api/vocabulary/impact":
                read = lambda relative: (ROOT / relative).read_text(encoding="utf-8")
                self._json(200, impact_index(read("ontology/core.ttl"), read("catalog/nac-usecases.ttl"), {slug: read(f"cases/{slug}/ontology.ttl") for slug in slugs()}, "lokaler Arbeitsstand"))
            elif path == "/api/vocabulary/turtle":
                self._json(200, {"turtle": (ROOT / "ontology/core.ttl").read_text(encoding="utf-8")})
            elif path in ("/", "/index.html", "/app.js", "/style.css"):
                filename = "index.html" if path == "/" else path.lstrip("/")
                types = {"index.html": "text/html", "app.js": "text/javascript", "style.css": "text/css"}
                self._send(200, (ASSETS / filename).read_bytes(), types[filename] + "; charset=utf-8")
            elif path in BRAND_ASSETS:
                self._send(200, (ASSETS / BRAND_ASSETS[path]).read_bytes(), "image/png")
            elif path in LEARNING_ASSETS:
                filename, kind = LEARNING_ASSETS[path]
                self._send(200, (ASSETS / filename).read_bytes(), kind)
            else:
                self._json(404, {"error": "Nicht gefunden"})
        except ValueError as exc:
            self._json(400, {"error": str(exc)})
        except Exception as exc:
            self._json(500, {"error": f"Serverfehler: {exc}"})

    def do_POST(self) -> None:
        try:
            host = self.headers.get("Host", "")
            origin = self.headers.get("Origin", "")
            if host != f"127.0.0.1:{self.server.server_port}" or origin != f"http://{host}":
                raise PermissionError("Ungültiger Ursprung")
            if self.headers.get("X-Editor-Token") != self.server.token:
                raise PermissionError("Ungültige Sitzung")
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= MAX_REQUEST or self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                raise ValueError("Ungültige Anfragegröße oder Inhaltstyp")
            data = json.loads(self.rfile.read(length))
            if self.path == "/api/start-branch":
                purpose = data.get("purpose", "case")
                self._json(200, {"branch": start_branch(purpose), "purpose": purpose})
            elif self.path == "/api/vocabulary/preview":
                _, changes, changed = prepare_vocabulary_change((ROOT / "ontology/core.ttl").read_text(encoding="utf-8"), data)
                self._json(200, {"changed": changed, "changes": changes})
            elif self.path == "/api/vocabulary/save":
                self._json(200, write_vocabulary_change(data))
            elif self.path == "/api/vocabulary/review":
                self._json(200, submit_vocabulary_review(data))
            elif self.path.startswith("/api/cases/") and self.path.endswith("/preview"):
                slug = self.path.split("/")[3]
                self._json(200, preview_change(slug, data))
            elif self.path.startswith("/api/cases/") and self.path.endswith("/restore-preview"):
                slug = self.path.split("/")[3]
                history, proposal = preview_local_case_restore(slug, data)
                self._json(200, {"changed": proposal["changed"], "changes": proposal["changes"], "main_ref": history["main_ref"], "target_sha": data["target_sha"]})
            elif self.path.startswith("/api/cases/") and self.path.endswith("/restore"):
                self._json(200, restore_local_case(self.path.split("/")[3], data))
            elif self.path.startswith("/api/cases/") and self.path.endswith("/review"):
                slug = self.path.split("/")[3]
                self._json(200, submit_review(slug, data))
            elif self.path.startswith("/api/cases/") and self.path.endswith("/save"):
                slug = self.path.split("/")[3]
                self._json(200, write_change(slug, data))
            else:
                self._json(404, {"error": "Nicht gefunden"})
        except PermissionError as exc:
            self._json(403, {"error": str(exc)})
        except (ValueError, json.JSONDecodeError) as exc:
            self._json(400, {"error": str(exc)})
        except Exception as exc:
            self._json(500, {"error": f"Serverfehler: {exc}"})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    slugs()  # Validate the explicit data checkout before opening the local server.
    with EditorServer(("127.0.0.1", args.port)) as server:
        url = f"http://127.0.0.1:{server.server_port}/"
        print(f"NaC-Fallontologie-Editor: {url}")
        print("Nur lokal erreichbar. Beenden mit Strg+C.")
        if not args.no_browser:
            webbrowser.open(url)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
