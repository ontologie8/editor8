# SPDX-License-Identifier: AGPL-3.0-or-later
"""Serve the real editor API with an in-memory GitHub substitute for browser tests.

No request made by this server reaches GitHub or writes into the repository.
The case models and catalog are loaded from the maintained Turtle files.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import sys
from threading import RLock
import time

from rdflib import Graph

from fixtures import DemoDataset
import os
DEMO = DemoDataset()
os.environ['EDITOR8_DATA_ROOT'] = str(DEMO.root)
APP_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_ROOT / "scripts"))
from case_editor_model import ROOT

import cloud_editor
from case_editor import preview_change
from case_editor_model import load_case, prepare_change, slugs
from case_index import build_case_index


MAIN_REF = "a" * 40
PORT = 18767
ORIGIN = f"http://127.0.0.1:{PORT}"


class BrowserStore:
    """Only the GitHub operations needed for a real browser editing path."""

    lock = RLock()
    branches: dict[str, dict] = {}

    def __init__(self, owner: str, repo: str, token: str):
        assert (owner, repo) in (("notariat8", "ontology"), ("example", "second-dataset")) and token == "browser-fixture"

    def slugs(self, ref):
        return slugs()

    def ref(self, branch: str) -> str:
        with self.lock:
            return MAIN_REF if branch == "main" else self.branches[branch]["sha"]

    def read_file(self, path: str, ref: str) -> str:
        if path != "catalog/nac-usecases.ttl":
            raise ValueError("Browser fixture supports only the case catalog")
        return (ROOT / path).read_text(encoding="utf-8")

    def list_drafts(self, username: str) -> list[dict]:
        return []

    def case_index(self, main_ref: str) -> dict:
        assert main_ref == MAIN_REF
        catalog = (ROOT / "catalog/nac-usecases.ttl").read_text(encoding="utf-8")
        cases = {slug: (ROOT / "cases" / slug / "ontology.ttl").read_text(encoding="utf-8") for slug in slugs()}
        return build_case_index(catalog, cases, main_ref)

    def create_branch(self, branch: str) -> str:
        with self.lock:
            if branch in self.branches:
                raise ValueError("Branch already exists")
            self.branches[branch] = {"sha": MAIN_REF, "model": None, "files": set()}
        return MAIN_REF

    def load_case(self, slug: str, branch: str) -> dict:
        with self.lock:
            saved = self.branches.get(branch, {}).get("model")
            if saved is not None and saved["slug"] == slug:
                model = deepcopy(saved)
            else:
                model = load_case(slug)
            model["expected_ref"] = self.ref(branch)
            return model

    def preview(self, slug: str, branch: str, data: dict) -> dict:
        if branch == "main" or self.ref(branch) != data.get("expected_ref"):
            raise ValueError("Arbeitszweig ist nicht aktuell")
        return preview_change(slug, data)

    def save(self, slug: str, branch: str, data: dict) -> dict:
        if branch == "main" or self.ref(branch) != data.get("expected_ref"):
            raise ValueError("Arbeitszweig ist nicht aktuell")
        ttl, page, changed = prepare_change(slug, data, data.get("revision", ""))
        if not changed:
            return {"changed": False, "revision": data["revision"], "expected_ref": self.ref(branch)}
        Graph().parse(data=ttl, format="turtle")
        assert page.strip()
        with self.lock:
            record = self.branches[branch]
            record["files"] = {f"cases/{slug}/ontology.ttl", f"cases/{slug}/README.md"}
            record["sha"] = hashlib.sha1(ttl.encode("utf-8")).hexdigest()
            record["model"] = deepcopy(data)
            record["model"]["revision"] = hashlib.sha256(ttl.encode("utf-8")).hexdigest()
            return {"changed": True, "revision": record["model"]["revision"], "expected_ref": record["sha"]}

    def create_pr(self, slug: str, branch: str, reason: str, source: str) -> str:
        with self.lock:
            record = self.branches[branch]
            if record["files"] != {f"cases/{slug}/ontology.ttl", f"cases/{slug}/README.md"}:
                raise ValueError("Unvollständige Falldateien")
            if len(reason.strip()) < 15 or len(source.strip()) < 5:
                raise ValueError("Fachlicher Grund und Quellenstand fehlen")
        return "https://github.com/notariat8/ontology/pull/123456"


class QuietBrowserHandler(cloud_editor.CloudHandler):
    def log_message(self, format: str, *args: object) -> None:
        pass


def main() -> None:
    cloud_editor.GitHubStore = BrowserStore
    def fake_github(url, token):
        assert token == "browser-fixture" and url in ("https://api.github.com/repos/notariat8/ontology", "https://api.github.com/repos/example/second-dataset")
        return {"permissions": {"push": True}}
    cloud_editor.github_json = fake_github
    server = cloud_editor.CloudServer(("127.0.0.1", PORT), {
        "GITHUB_APP_CLIENT_ID": "browser-fixture",
        "GITHUB_APP_CLIENT_SECRET": "browser-fixture",
        "GITHUB_REPOSITORY": "notariat8/ontology",
        "PUBLIC_ORIGIN": ORIGIN,
        "EDITOR_USERS": "browser-tester",
        "DATA_REPOSITORIES": [{"repository": "notariat8/ontology", "label": "Künstlicher Datensatz eins"}, {"repository": "example/second-dataset", "label": "Künstlicher Datensatz zwei"}],
    })
    server.RequestHandlerClass = QuietBrowserHandler
    server.sessions["browser-session"] = {
        "token": "browser-fixture", "user": "browser-tester", "csrf": "browser-csrf",
        "branch": "main", "created": time.time(),
    }
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
