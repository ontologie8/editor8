# SPDX-License-Identifier: AGPL-3.0-or-later
"""GitHub-backed storage for one shared NaC ontology repository.

Case changes commit Turtle plus their generated reading page; vocabulary
changes commit only core Turtle. Each operation
uses an isolated temporary model root, so concurrent editors never switch a
shared Git checkout or overwrite each other's work in server memory.
"""

from __future__ import annotations

import base64
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import json
from pathlib import Path
import re
from tempfile import TemporaryDirectory
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

from rdflib import Graph
from rdflib.compare import to_isomorphic

from data_contract import parse_baseline
from case_editor_model import _graph_to_model, graph_from_model, load_case, prepare_change
from case_editor import describe_changes, preview_change
from case_restore import prepare_historical_case
from case_index import build_case_index
from case_document import render
from vocabulary_editor import model as vocabulary_model, prepare_change as prepare_vocabulary_change
from vocabulary_impact import impact_index


NAME = re.compile(r"[A-Za-z0-9_.-]+\Z")
BRANCH = re.compile(r"codex/ontology-(?:editor|vocabulary)-[A-Za-z0-9_.-]+\Z")
SHA = re.compile(r"[0-9a-f]{40}\Z")


class GitHubError(ValueError):
    def __init__(self, status: int, message: str):
        self.status = status
        super().__init__(message)


class GitHubStore:
    def __init__(self, owner: str, repo: str, token: str):
        if not NAME.fullmatch(owner) or not NAME.fullmatch(repo) or not token:
            raise ValueError("Ungültige Repository-Konfiguration")
        if f"{owner}/{repo}".lower() == "ontologie8/editor8":
            raise ValueError("Das Software-Repository darf kein Datenziel sein")
        self._baselines = {}
        self.base = f"https://api.github.com/repos/{owner}/{repo}"
        self.owner = owner
        self.repo = repo
        self.token = token

    def baseline(self, commit_ref: str) -> dict:
        # A branch name is resolved first; snapshots always read an immutable commit.
        if not SHA.fullmatch(commit_ref):
            commit_ref = self.ref(commit_ref)
        if commit_ref not in self._baselines:
            self._baselines[commit_ref] = parse_baseline(self.read_file("catalog/nac-baseline.json", commit_ref))
        return self._baselines[commit_ref]

    def slugs(self, commit_ref: str) -> list[str]:
        return list(self.baseline(commit_ref)["business_case_type_ids"])

    def request(self, method: str, path: str, payload: dict | None = None) -> dict | list:
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": "2026-03-10",
            "User-Agent": "NaC-ontology-editor",
        }
        if body is not None:
            headers["Content-Type"] = "application/json"
        req = Request(self.base + path, data=body, headers=headers, method=method)
        try:
            with urlopen(req, timeout=20) as response:
                return json.load(response)
        except HTTPError as error:
            try:
                message = json.load(error).get("message", "GitHub-Anfrage fehlgeschlagen")
            except (ValueError, OSError):
                message = "GitHub-Anfrage fehlgeschlagen"
            raise GitHubError(error.code, message) from None

    def ref(self, branch: str) -> str:
        if branch != "main" and not BRANCH.fullmatch(branch):
            raise ValueError("Ungültiger Arbeitszweig")
        result = self.request("GET", "/git/ref/heads/" + quote(branch, safe="/"))
        return result["object"]["sha"]

    def read_file(self, path: str, branch: str) -> str:
        result = self.request("GET", "/contents/" + quote(path, safe="/") + "?ref=" + quote(branch, safe=""))
        if result.get("encoding") != "base64":
            raise ValueError("GitHub lieferte keine Datei")
        return base64.b64decode(result["content"]).decode("utf-8")

    def create_branch(self, branch: str) -> str:
        if not BRANCH.fullmatch(branch):
            raise ValueError("Ungültiger Arbeitszweig")
        sha = self.ref("main")
        self.request("POST", "/git/refs", {"ref": "refs/heads/" + branch, "sha": sha})
        return sha

    def list_drafts(self, username: str) -> list[dict]:
        """Find this user's saved editor branches that have not entered a PR."""
        if not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?", username):
            raise ValueError("Ungültiges GitHub-Konto")
        refs = self.request("GET", "/git/matching-refs/heads/codex/ontology-")
        prefix = "refs/heads/"
        pattern = re.compile(r"codex/ontology-(editor|vocabulary)-" + re.escape(username) + r"-[0-9]{14}-[0-9a-f]{6}\Z", re.IGNORECASE)
        branches = sorted((ref["ref"][len(prefix):] for ref in refs if isinstance(ref.get("ref"), str) and ref["ref"].startswith(prefix) and pattern.fullmatch(ref["ref"][len(prefix):])), reverse=True)
        if len(branches) > 50:
            raise ValueError("Zu viele Arbeitsentwürfe. Bitte alte Zweige in GitHub prüfen.")
        drafts = []
        for branch in branches:
            comparison = self.request("GET", "/compare/main..." + quote(branch, safe="/"))
            files = comparison.get("files", [])
            if any(item.get("status") not in {"modified", "added"} for item in files):
                continue
            paths = {item.get("filename") for item in files}
            if comparison.get("total_commits") == 0 and not files:
                purpose = "vocabulary" if branch.startswith("codex/ontology-vocabulary-") else "case"
                slug = ""
            elif comparison.get("total_commits", 0) < 1:
                continue
            elif paths == {"ontology/core.ttl"} and branch.startswith("codex/ontology-vocabulary-"):
                purpose, slug = "vocabulary", ""
            else:
                matches = [slug for slug in self.slugs("main") if paths == {f"cases/{slug}/ontology.ttl", f"cases/{slug}/README.md"}]
                if len(matches) != 1 or not branch.startswith("codex/ontology-editor-"):
                    continue
                purpose, slug = "case", matches[0]
            head = quote(f"{self.owner}:{branch}", safe="")
            if self.request("GET", f"/pulls?state=all&head={head}&per_page=1"):
                continue
            drafts.append({"branch": branch, "purpose": purpose, "case": slug})
        return drafts

    @contextmanager
    def model_root(self, slug: str, commit_ref: str):
        baseline = self.baseline(commit_ref)
        if slug not in baseline["business_case_type_ids"]:
            raise ValueError("Unbekannter Fall")
        source = self.read_file(f"cases/{slug}/ontology.ttl", commit_ref)
        catalog = self.read_file("catalog/nac-usecases.ttl", commit_ref)
        with TemporaryDirectory(prefix="nac-editor-") as location:
            root = Path(location)
            (root / "catalog").mkdir()
            (root / "cases" / slug).mkdir(parents=True)
            (root / "catalog/nac-baseline.json").write_text(json.dumps(baseline), encoding="utf-8")
            (root / "catalog/nac-usecases.ttl").write_text(catalog, encoding="utf-8")
            (root / "cases" / slug / "ontology.ttl").write_text(source, encoding="utf-8")
            yield root

    def load_case(self, slug: str, branch: str) -> dict:
        head = self.ref(branch)
        with self.model_root(slug, head) as root:
            model = load_case(slug, root)
        model["expected_ref"] = head
        return model

    def preview(self, slug: str, branch: str, data: dict) -> dict:
        head = self.ref(branch)
        if head != data.get("expected_ref"):
            raise ValueError("Der Arbeitszweig wurde inzwischen geändert. Fall neu laden.")
        with self.model_root(slug, head) as root:
            return preview_change(slug, data, root)

    def save(self, slug: str, branch: str, data: dict) -> dict:
        if not branch.startswith("codex/ontology-editor-"):
            raise ValueError("Auf main kann nicht gespeichert werden")
        parent = self.ref(branch)
        if parent != data.get("expected_ref"):
            raise ValueError("Der Arbeitszweig wurde inzwischen geändert. Fall neu laden.")
        with self.model_root(slug, parent) as root:
            ttl, page, changed = prepare_change(slug, data, data.get("revision", ""), root)
        if not changed:
            return {"changed": False, "revision": data["revision"], "expected_ref": parent}
        self._commit_files(branch, parent, {
            f"cases/{slug}/ontology.ttl": ttl, f"cases/{slug}/README.md": page,
        }, f"Propose ontology change for {slug}")
        refreshed = self.load_case(slug, branch)
        return {"changed": True, "revision": refreshed["revision"], "expected_ref": refreshed["expected_ref"]}

    def create_pr(self, slug: str, branch: str, reason: str, source: str) -> str:
        if not branch.startswith("codex/ontology-editor-") or not BRANCH.fullmatch(branch):
            raise ValueError("Ungültiger Arbeitszweig")
        self._check_pr_files(branch, {f"cases/{slug}/ontology.ttl", f"cases/{slug}/README.md"})
        if not isinstance(reason, str) or not isinstance(source, str) or not 15 <= len(reason.strip()) <= 3000 or not 5 <= len(source.strip()) <= 1000:
            raise ValueError("Fachlicher Grund und Quellenstand fehlen")
        title = f"Fachliche Änderung: {self.load_case(slug, branch)['title']}"
        body = f"## Fachlicher Grund\n\n{reason.strip()}\n\n## Quellenstand\n\n{source.strip()}\n\n## Freigabe\n\nNotarielle Fachprüfung ausstehend.\n"
        result = self.request("POST", "/pulls", {"title": title, "head": branch, "base": "main", "body": body, "draft": False})
        return result["html_url"]

    def _commit_files(self, branch: str, parent: str, files: dict[str, str], message: str) -> None:
        new_sha = self._create_commit(parent, files, message)
        self.request("PATCH", "/git/refs/heads/" + quote(branch, safe="/"), {"sha": new_sha, "force": False})

    def _create_commit(self, parent: str, files: dict[str, str], message: str) -> str:
        commit = self.request("GET", "/git/commits/" + parent)
        tree = self.request("POST", "/git/trees", {
            "base_tree": commit["tree"]["sha"],
            "tree": [{"path": path, "mode": "100644", "type": "blob", "content": content} for path, content in files.items()],
        })
        new_commit = self.request("POST", "/git/commits", {
            "message": message, "tree": tree["sha"], "parents": [parent]
        })
        return new_commit["sha"]

    def case_history(self, slug: str, main_ref: str | None = None) -> dict:
        main_ref = main_ref or self.ref("main")
        if slug not in self.slugs(main_ref):
            raise ValueError("Unbekannter Fall")
        if not SHA.fullmatch(main_ref):
            raise ValueError("Ungültiger Katalog-Commit")
        path = f"cases/{slug}/ontology.ttl"
        commits = self.request("GET", "/commits?sha=" + main_ref + "&path=" + quote(path, safe="/") + "&per_page=20")
        entries = []
        for item in commits:
            sha = item.get("sha", "")
            if not SHA.fullmatch(sha):
                raise ValueError("GitHub lieferte einen ungültigen historischen Commit")
            metadata = item.get("commit") or {}
            author = metadata.get("author") or {}
            entries.append({
                "sha": sha,
                "message": (metadata.get("message") or "").split("\n", 1)[0],
                "author": (item.get("author") or {}).get("login") or author.get("name") or "unbekannt",
                "date": author.get("date") or "",
                "url": f"https://github.com/{self.owner}/{self.repo}/commit/{sha}",
            })
        return {"main_ref": main_ref, "case": slug, "entries": entries}

    def _historical_case(self, slug: str, target_sha: str, main_ref: str) -> dict:
        if not SHA.fullmatch(target_sha) or target_sha not in {entry["sha"] for entry in self.case_history(slug, main_ref)["entries"]}:
            raise ValueError("Die frühere Fassung ist nicht in der angezeigten Fallhistorie")
        historical = self.read_file(f"cases/{slug}/ontology.ttl", target_sha)
        with self.model_root(slug, main_ref) as root:
            return prepare_historical_case(slug, historical, root, describe_changes)

    def preview_case_restore(self, slug: str, target_sha: str, expected_main: str) -> dict:
        if not SHA.fullmatch(expected_main) or self.ref("main") != expected_main:
            raise ValueError("Der Katalog wurde inzwischen geändert. Fall und Historie neu laden.")
        proposal = self._historical_case(slug, target_sha, expected_main)
        return {"changed": proposal["changed"], "changes": proposal["changes"], "main_ref": expected_main, "target_sha": target_sha}

    def restore_case(self, slug: str, target_sha: str, expected_main: str, branch: str) -> dict:
        if not BRANCH.fullmatch(branch) or not branch.startswith("codex/ontology-editor-"):
            raise ValueError("Ungültiger Arbeitszweig")
        if not SHA.fullmatch(expected_main) or self.ref("main") != expected_main:
            raise ValueError("Der Katalog wurde inzwischen geändert. Fall und Historie neu laden.")
        proposal = self._historical_case(slug, target_sha, expected_main)
        if not proposal["changed"]:
            raise ValueError("Die frühere Fassung entspricht bereits dem aktuellen Fall")
        new_sha = self._create_commit(expected_main, {
            f"cases/{slug}/ontology.ttl": proposal["turtle"],
            f"cases/{slug}/README.md": proposal["page"],
        }, f"Propose historical case version for {slug}")
        self.request("POST", "/git/refs", {"ref": "refs/heads/" + branch, "sha": new_sha})
        return {"branch": branch, "expected_ref": new_sha, "changes": proposal["changes"]}

    def _check_pr_files(self, branch: str, expected: set[str]) -> None:
        comparison = self.request("GET", "/compare/main..." + quote(branch, safe="/"))
        files = comparison.get("files", [])
        actual = {item["filename"] for item in files}
        if comparison.get("total_commits", 0) < 1 or actual != expected or any(item.get("status") not in {"modified", "added"} for item in files):
            raise ValueError("Der Arbeitszweig enthält keine passende oder weitere Änderungen")

    def load_vocabulary(self, branch: str) -> dict:
        head = self.ref(branch)
        result = vocabulary_model(self.read_file("ontology/core.ttl", head))
        result["expected_ref"] = head
        return result

    def _case_snapshot(self, main_ref: str) -> tuple[str, dict[str, str]]:
        if not SHA.fullmatch(main_ref):
            raise ValueError("Ungültiger Katalog-Commit")
        paths = ["catalog/nac-usecases.ttl", *(f"cases/{slug}/ontology.ttl" for slug in self.slugs(main_ref))]
        with ThreadPoolExecutor(max_workers=5) as pool:
            texts = dict(zip(paths, pool.map(lambda path: self.read_file(path, main_ref), paths)))
        return texts["catalog/nac-usecases.ttl"], {slug: texts[f"cases/{slug}/ontology.ttl"] for slug in self.slugs(main_ref)}

    def case_index(self, main_ref: str | None = None) -> dict:
        main_ref = main_ref or self.ref("main")
        catalog, cases = self._case_snapshot(main_ref)
        return build_case_index(catalog, cases, main_ref, self.slugs(main_ref))

    def vocabulary_impact(self, main_ref: str | None = None) -> dict:
        main_ref = main_ref or self.ref("main")
        if not SHA.fullmatch(main_ref):
            raise ValueError("Ungültiger Katalog-Commit für die Auswirkungsübersicht")
        catalog, cases = self._case_snapshot(main_ref)
        core = self.read_file("ontology/core.ttl", main_ref)
        return impact_index(core, catalog, cases, main_ref, self.slugs(main_ref))

    def preview_vocabulary(self, branch: str, data: dict) -> dict:
        head = self.ref(branch)
        if head != data.get("expected_ref"):
            raise ValueError("Der Arbeitszweig wurde inzwischen geändert. Vokabular neu laden.")
        from graph_comparison import vocabulary_comparison
        original = self.read_file("ontology/core.ttl", head)
        updated, changes, changed = prepare_vocabulary_change(original, data)
        return {"changed": changed, "changes": changes, "comparison": vocabulary_comparison(original, updated)}

    def save_vocabulary(self, branch: str, data: dict) -> dict:
        if not branch.startswith("codex/ontology-vocabulary-") or not BRANCH.fullmatch(branch):
            raise ValueError("Für das Vokabular ist ein eigener Arbeitszweig erforderlich")
        parent = self.ref(branch)
        if parent != data.get("expected_ref"):
            raise ValueError("Der Arbeitszweig wurde inzwischen geändert. Vokabular neu laden.")
        original = self.read_file("ontology/core.ttl", parent)
        ttl, _, changed = prepare_vocabulary_change(original, data)
        if changed:
            self._commit_files(branch, parent, {"ontology/core.ttl": ttl}, "Propose shared ontology vocabulary change")
        refreshed = self.load_vocabulary(branch)
        return {"changed": changed, "revision": refreshed["revision"], "expected_ref": refreshed["expected_ref"]}

    def create_vocabulary_pr(self, branch: str, reason: str, source: str) -> str:
        if not branch.startswith("codex/ontology-vocabulary-") or not BRANCH.fullmatch(branch):
            raise ValueError("Ungültiger Vokabular-Arbeitszweig")
        if not isinstance(reason, str) or not isinstance(source, str) or not 15 <= len(reason.strip()) <= 3000 or not 5 <= len(source.strip()) <= 1000:
            raise ValueError("Fachlicher Grund und Quellenstand fehlen")
        self._check_pr_files(branch, {"ontology/core.ttl"})
        body = f"## Fachlicher Grund\n\n{reason.strip()}\n\n## Quellenstand\n\n{source.strip()}\n\n## Freigabe\n\nNotarielle Fachprüfung ausstehend.\n"
        result = self.request("POST", "/pulls", {"title": "Fachliche Änderung: gemeinsames Vokabular", "head": branch, "base": "main", "body": body, "draft": False})
        return result["html_url"]

    def _case_pr(self, number: int) -> tuple[dict, str]:
        if not isinstance(number, int) or not 0 < number < 1_000_000:
            raise ValueError("Ungültige Pull-Request-Nummer")
        pr = self.request("GET", f"/pulls/{number}")
        if pr.get("state") != "open" or pr.get("base", {}).get("ref") != "main":
            raise ValueError("Dieser Pull Request ist nicht zur Fallprüfung offen")
        if (pr.get("head", {}).get("repo") or {}).get("full_name", "").lower() != f"{self.owner}/{self.repo}".lower():
            raise ValueError("Nur Änderungen aus diesem Repository sind im Prüfkorb verfügbar")
        if pr.get("changed_files") != 2:
            raise ValueError("Dieser Pull Request enthält weitere Dateien und muss in GitHub geprüft werden")
        files = self.request("GET", f"/pulls/{number}/files?per_page=100")
        filenames = {file["filename"] for file in files}
        found = [slug for slug in self.slugs(pr["head"]["sha"]) if filenames == {f"cases/{slug}/ontology.ttl", f"cases/{slug}/README.md"}]
        if len(found) != 1:
            raise ValueError("Dieser Pull Request ist kein einzelner NaC-Fall")
        return pr, found[0]

    def _vocabulary_pr(self, number: int) -> dict:
        if not isinstance(number, int) or not 0 < number < 1_000_000:
            raise ValueError("Ungültige Pull-Request-Nummer")
        pr = self.request("GET", f"/pulls/{number}")
        if pr.get("state") != "open" or pr.get("base", {}).get("ref") != "main":
            raise ValueError("Dieser Pull Request ist nicht zur Fachprüfung offen")
        if (pr.get("head", {}).get("repo") or {}).get("full_name", "").lower() != f"{self.owner}/{self.repo}".lower():
            raise ValueError("Nur Änderungen aus diesem Repository sind im Prüfkorb verfügbar")
        if pr.get("changed_files") != 1:
            raise ValueError("Dieser Pull Request enthält weitere Dateien")
        files = self.request("GET", f"/pulls/{number}/files?per_page=100")
        if {file["filename"] for file in files} != {"ontology/core.ttl"}:
            raise ValueError("Dieser Pull Request ändert nicht das gemeinsame Vokabular")
        return pr

    def list_case_reviews(self) -> list[dict]:
        pulls = self.request("GET", "/pulls?state=open&base=main&per_page=100")
        reviews = []
        for pr in pulls:
            try:
                checked, slug = self._case_pr(pr["number"])
            except ValueError:
                try:
                    checked, slug = self._vocabulary_pr(pr["number"]), "vocabulary"
                except ValueError:
                    continue
            reviews.append({
                "number": checked["number"], "title": checked["title"], "case": slug,
                "author": checked["user"]["login"], "draft": checked["draft"],
                "url": checked["html_url"], "updated_at": checked["updated_at"],
            })
        return reviews

    def review_detail(self, number: int) -> dict:
        try:
            pr, slug = self._case_pr(number)
        except ValueError:
            pr, slug = self._vocabulary_pr(number), "vocabulary"
        base, head = pr["base"]["sha"], pr["head"]["sha"]
        if not SHA.fullmatch(base) or not SHA.fullmatch(head):
            raise ValueError("GitHub lieferte keinen gültigen Commit-Stand")
        comparison = self.request("GET", f"/compare/{base}...{head}")
        merge_base = comparison["merge_base_commit"]["sha"]
        if not SHA.fullmatch(merge_base):
            raise ValueError("GitHub lieferte keinen gültigen Vergleichsstand")
        path = "ontology/core.ttl" if slug == "vocabulary" else f"cases/{slug}/ontology.ttl"
        before_text = self.read_file(path, merge_base)
        after_text = self.read_file(path, head)
        changes = []
        problem = ""
        graph_comparison = None
        try:
            from graph_comparison import case_comparison, vocabulary_comparison
            if slug == "vocabulary":
                graph_comparison = vocabulary_comparison(before_text, after_text)
                old_model, new_model = vocabulary_model(before_text), vocabulary_model(after_text)
                reconstructed, changes, _ = prepare_vocabulary_change(before_text, {**new_model, "revision": old_model["revision"]})
                if to_isomorphic(Graph().parse(data=reconstructed, format="turtle")) != to_isomorphic(Graph().parse(data=after_text, format="turtle")):
                    problem = "Zusätzliche RDF-Änderungen sind in dieser Ansicht nicht vollständig erklärt. Bitte in GitHub prüfen."
            else:
                graph_comparison = case_comparison(slug, before_text, after_text)
                before = Graph().parse(data=before_text, format="turtle")
                after = Graph().parse(data=after_text, format="turtle")
                old_model, new_model = _graph_to_model(slug, before), _graph_to_model(slug, after)
                changes = describe_changes(old_model, new_model)
                reconstructed = graph_from_model(slug, new_model, before)
                if to_isomorphic(reconstructed) != to_isomorphic(after):
                    problem = "Zusätzliche RDF-Änderungen sind in dieser Ansicht nicht vollständig erklärt. Bitte in GitHub prüfen."
                else:
                    with self.model_root(slug, head) as root:
                        if self.read_file(f"cases/{slug}/README.md", head) != render(slug, after, root=root):
                            problem = "Die Mermaid-Leseseite stimmt nicht mit Turtle überein."
        except GitHubError:
            raise
        except Exception:
            problem = "Die Falländerung konnte fachlich nicht vollständig gelesen werden. Bitte die Turtle-Datei in GitHub prüfen."
        if not changes and not problem:
            problem = "Keine fachliche Änderung erkennbar. Bitte den GitHub-Diff prüfen."
        return {
            "number": number, "title": pr["title"], "case": slug,
            "author": pr["user"]["login"], "draft": pr["draft"],
            "url": pr["html_url"], "body": pr.get("body") or "",
            "head_sha": head, "changes": changes, "problem": problem, "comparison": graph_comparison,
        }

    def submit_case_review(self, number: int, head_sha: str, event: str, body: str, reviewer: str, notaries: set[str], checks: dict | None = None) -> str:
        detail = self.review_detail(number)
        if detail["head_sha"] != head_sha:
            raise ValueError("Die Änderung hat inzwischen einen neuen Stand. Bitte neu laden.")
        if detail["draft"] or (event == "APPROVE" and detail["problem"]):
            raise ValueError("Dieser Pull Request ist noch nicht fachlich freigabefähig")
        if detail["author"].lower() == reviewer.lower():
            raise ValueError("Eigene Änderungen können hier nicht selbst geprüft werden")
        if event not in {"APPROVE", "REQUEST_CHANGES"} or not isinstance(body, str) or not 15 <= len(body.strip()) <= 3000:
            raise ValueError("Prüfentscheidung und Begründung fehlen")
        if event == "APPROVE" and reviewer.lower() not in notaries:
            raise PermissionError("Fachliche Freigabe ist nur für eingetragene Notarkonten möglich")
        if event == "APPROVE":
            if not isinstance(checks, dict) or any(checks.get(key) is not True for key in ("terms", "sources", "relations")):
                raise ValueError("Begriffe, Quellen und Beziehungen müssen als geprüft bestätigt werden")
            body = "Fachlich geprüft: Begriffe und Fachfragen; Rechtsquellen und Quellenstand; Beziehungen und fachliche Wirkung.\n\n" + body.strip()
        result = self.request("POST", f"/pulls/{number}/reviews", {
            "commit_id": head_sha, "event": event, "body": body.strip(),
        })
        return result["html_url"]
