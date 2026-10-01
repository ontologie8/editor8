# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check atomic GitHub case updates without making network requests."""

from contextlib import nullcontext
import base64
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from case_editor_model import ROOT, load_case, prepare_change
from github_store import GitHubStore
from vocabulary_editor import model as vocabulary_model, prepare_change as prepare_vocabulary_change


class GitHubStoreTests(unittest.TestCase):
    def setUp(self):
        # Existing behavior tests use the external dataset; contract reads are tested separately.
        baseline = json.loads((ROOT / "catalog/nac-baseline.json").read_text(encoding="utf-8"))
        patcher = patch.object(GitHubStore, "baseline", return_value=baseline)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_empty_own_branch_can_be_reopened_after_leaving(self):
        store = GitHubStore("notariat8", "ontology", "fake-token")
        branch = "codex/ontology-editor-reviewer-20260929100000-a1b2c3"

        def request(method, path, payload=None):
            if path == "/git/matching-refs/heads/codex/ontology-":
                return [{"ref": "refs/heads/" + branch}]
            if path.startswith("/compare/main..."):
                return {"total_commits": 0, "files": []}
            if path.startswith("/pulls?"):
                return []
            raise AssertionError(path)

        with patch.object(store, "request", side_effect=request):
            self.assertEqual(store.list_drafts("reviewer"), [{"branch": branch, "purpose": "case", "case": ""}])

    def test_saved_drafts_are_own_unsubmitted_single_scope_branches(self):
        store = GitHubStore("notariat8", "ontology", "fake-token")
        case = "codex/ontology-editor-reviewer-20260929100000-a1b2c3"
        vocabulary = "codex/ontology-vocabulary-reviewer-20260929110000-d4e5f6"
        other = "codex/ontology-editor-other-20260929120000-a1b2c3"
        seen = []

        def request(method, path, payload=None):
            seen.append(path)
            if path == "/git/matching-refs/heads/codex/ontology-":
                return [{"ref": "refs/heads/" + branch} for branch in (case, vocabulary, other)]
            if path.startswith("/compare/main..."):
                files = ["ontology/core.ttl"] if "vocabulary" in path else ["cases/erbausschlagung/ontology.ttl", "cases/erbausschlagung/README.md"]
                return {"total_commits": 1, "files": [{"filename": name, "status": "modified"} for name in files]}
            if path.startswith("/pulls?"):
                return [{"number": 17}] if "vocabulary" in path else []
            raise AssertionError(path)

        with patch.object(store, "request", side_effect=request):
            self.assertEqual(store.list_drafts("reviewer"), [{"branch": case, "purpose": "case", "case": "erbausschlagung"}])
        self.assertFalse(any(other in path for path in seen[1:]))
        with self.assertRaisesRegex(ValueError, "GitHub-Konto"):
            store.list_drafts("../other")

    def test_case_history_is_limited_to_one_case_and_pinned_main(self):
        store = GitHubStore("notariat8", "ontology", "fake-token")
        main, older = "a" * 40, "b" * 40
        record = {"sha": older, "commit": {"message": "Fachfrage angepasst\nDetails", "author": {"name": "Notariat", "date": "2026-09-28T10:00:00Z"}}}
        with patch.object(store, "request", return_value=[record]) as request:
            history = store.case_history("erbausschlagung", main)
        request.assert_called_once_with("GET", f"/commits?sha={main}&path=cases/erbausschlagung/ontology.ttl&per_page=20")
        self.assertEqual(history["main_ref"], main)
        self.assertEqual(history["entries"][0]["message"], "Fachfrage angepasst")
        self.assertEqual(history["entries"][0]["url"], f"https://github.com/notariat8/ontology/commit/{older}")

    def test_case_and_vocabulary_reads_use_the_resolved_commit(self):
        store = GitHubStore("notariat8", "ontology", "fake-token")
        head = "a" * 40
        reads = []

        def read_file(path, ref):
            reads.append((path, ref))
            return (ROOT / path).read_text(encoding="utf-8")

        with (patch.object(store, "ref", return_value=head), patch.object(store, "read_file", side_effect=read_file)):
            case = store.load_case("immobilienkaufvertrag", "codex/ontology-editor-test")
            self.assertEqual(case["expected_ref"], head)
            self.assertFalse(store.preview("immobilienkaufvertrag", "codex/ontology-editor-test", case)["changed"])
            vocabulary = store.load_vocabulary("codex/ontology-vocabulary-test")
            self.assertEqual(vocabulary["expected_ref"], head)
            self.assertFalse(store.preview_vocabulary("codex/ontology-vocabulary-test", vocabulary)["changed"])
        self.assertEqual({ref for _, ref in reads}, {head})
        self.assertEqual({path for path, _ in reads}, {"cases/immobilienkaufvertrag/ontology.ttl", "catalog/nac-usecases.ttl", "ontology/core.ttl"})

    def test_case_index_reads_all_cases_at_one_main_commit(self):
        from case_editor_model import slugs
        store = GitHubStore("notariat8", "ontology", "fake-token")
        paths = ["catalog/nac-usecases.ttl", *(f"cases/{slug}/ontology.ttl" for slug in slugs())]
        texts = {path: (ROOT / path).read_text(encoding="utf-8") for path in paths}
        seen = []

        def read_file(path, ref):
            seen.append((path, ref))
            return texts[path]

        with (patch.object(store, "ref", return_value="a" * 40), patch.object(store, "read_file", side_effect=read_file)):
            result = store.case_index()
        self.assertEqual({path for path, _ in seen}, set(paths))
        self.assertEqual({ref for _, ref in seen}, {"a" * 40})
        self.assertEqual(len(result["entries"]), 392)

    def test_vocabulary_impact_reads_all_cases_at_one_main_commit(self):
        from case_editor_model import slugs
        store = GitHubStore("notariat8", "ontology", "fake-token")
        paths = ["ontology/core.ttl", "catalog/nac-usecases.ttl", *(f"cases/{slug}/ontology.ttl" for slug in slugs())]
        texts = {path: (ROOT / path).read_text(encoding="utf-8") for path in paths}
        seen = []

        def read_file(path, ref):
            seen.append((path, ref))
            return texts[path]

        with (patch.object(store, "ref", return_value="a" * 40), patch.object(store, "read_file", side_effect=read_file)):
            result = store.vocabulary_impact()
        self.assertEqual({path for path, _ in seen}, set(paths))
        self.assertEqual({ref for _, ref in seen}, {"a" * 40})
        self.assertEqual(result["source_ref"], "a" * 40)
        self.assertEqual(len(result["terms"]["Angabenfrage"]), 20)

    def test_pull_request_file_scope_rejects_extra_or_removed_files(self):
        store = GitHubStore("notariat8", "ontology", "fake-token")
        branch = "codex/ontology-vocabulary-test"
        with patch.object(store, "request", return_value={"total_commits": 1, "files": [{"filename": "ontology/core.ttl", "status": "modified"}]}):
            store._check_pr_files(branch, {"ontology/core.ttl"})
        for files in ([{"filename": "ontology/core.ttl", "status": "removed"}], [{"filename": "ontology/core.ttl", "status": "modified"}, {"filename": "README.md", "status": "modified"}]):
            with patch.object(store, "request", return_value={"total_commits": 1, "files": files}):
                with self.assertRaisesRegex(ValueError, "weitere Änderungen"):
                    store._check_pr_files(branch, {"ontology/core.ttl"})

    def test_vocabulary_write_and_notary_review(self):
        original = (ROOT / "ontology/core.ttl").read_text(encoding="utf-8")
        model = vocabulary_model(original)
        next(item for item in model["terms"] if item["id"] == "Dokumenttyp")["comment"] = "Abstrakte Art eines benötigten Dokuments."
        model["expected_ref"] = "parent"
        changed_ttl, changes, changed = prepare_vocabulary_change(original, model)
        self.assertTrue(changed)
        store = GitHubStore("notariat8", "ontology", "fake-token")
        base, head = "a" * 40, "b" * 40
        pr = {"number": 17, "title": "Gemeinsames Vokabular", "state": "open", "base": {"ref": "main", "sha": base}, "head": {"sha": head, "repo": {"full_name": "notariat8/ontology"}}, "changed_files": 1, "draft": False, "user": {"login": "author"}, "html_url": "https://github.com/notariat8/ontology/pull/17", "body": "Grund und Quelle", "updated_at": "2026-09-28T00:00:00Z"}
        written = []

        def request(method, path, payload=None):
            if (method, path) == ("GET", "/git/commits/parent"):
                return {"tree": {"sha": "old-tree"}}
            if (method, path) == ("POST", "/git/trees"):
                written.extend(payload["tree"])
                return {"sha": "new-tree"}
            if (method, path) == ("POST", "/git/commits"):
                return {"sha": "new-commit"}
            if method == "PATCH":
                return {}
            if (method, path) == ("GET", "/pulls?state=open&base=main&per_page=100"):
                return [{"number": 17}]
            if (method, path) == ("GET", "/pulls/17"):
                return pr
            if (method, path) == ("GET", "/pulls/17/files?per_page=100"):
                return [{"filename": "ontology/core.ttl"}]
            if (method, path) == ("GET", f"/compare/{base}...{head}"):
                return {"merge_base_commit": {"sha": base}}
            if method == "GET" and path.startswith("/contents/ontology/core.ttl?ref="):
                content = original if path.endswith(base) else changed_ttl
                return {"encoding": "base64", "content": base64.b64encode(content.encode()).decode()}
            if (method, path) == ("POST", "/pulls/17/reviews"):
                return {"html_url": "https://github.com/notariat8/ontology/pull/17#pullrequestreview-1"}
            raise AssertionError((method, path))

        refs = []
        def read_for_save(path, ref):
            refs.append(ref)
            return original if ref == "parent" else changed_ttl

        with (patch.object(store, "ref", side_effect=["parent", "new-commit"]), patch.object(store, "read_file", side_effect=read_for_save), patch.object(store, "request", side_effect=request)):
            result = store.save_vocabulary("codex/ontology-vocabulary-test", model)
        self.assertTrue(result["changed"])
        self.assertEqual(refs, ["parent", "new-commit"])
        self.assertEqual({item["path"] for item in written}, {"ontology/core.ttl"})
        with patch.object(store, "request", side_effect=request), patch.object(store, "model_root", return_value=nullcontext(ROOT)):
            self.assertEqual(store.list_case_reviews()[0]["case"], "vocabulary")
            detail = store.review_detail(17)
            self.assertEqual(detail["problem"], "")
            self.assertEqual(detail["changes"], changes)
            with self.assertRaisesRegex(PermissionError, "Notarkonten"):
                store.submit_case_review(17, head, "APPROVE", "Fachlich gründlich geprüft", "reviewer", set())
            self.assertIn("pullrequestreview", store.submit_case_review(17, head, "APPROVE", "Fachlich gründlich geprüft", "reviewer", {"reviewer"}, {"terms": True, "sources": True, "relations": True}))

    def test_save_writes_only_case_turtle_and_generated_page(self):
        store = GitHubStore("notariat8", "ontology", "fake-token")
        model = load_case("immobilienkaufvertrag")
        model["nodes"][0]["label"] = "Geänderte Fachbezeichnung"
        model["expected_ref"] = "parent"
        calls = []

        def request(method, path, payload=None):
            calls.append((method, path, payload))
            if method == "GET" and path == "/git/commits/parent":
                return {"tree": {"sha": "old-tree"}}
            if method == "POST" and path == "/git/trees":
                return {"sha": "new-tree"}
            if method == "POST" and path == "/git/commits":
                return {"sha": "new-commit"}
            if method == "PATCH":
                return {}
            raise AssertionError((method, path))

        model_refs = []
        def root_at_ref(slug, ref):
            model_refs.append(ref)
            return nullcontext(ROOT)

        with (
            patch.object(store, "ref", side_effect=["parent", "new-commit"]),
            patch.object(store, "model_root", side_effect=root_at_ref),
            patch.object(store, "request", side_effect=request),
        ):
            result = store.save("immobilienkaufvertrag", "codex/ontology-editor-test", model)
        tree = next(payload for method, path, payload in calls if path == "/git/trees")
        self.assertEqual(tree["base_tree"], "old-tree")
        self.assertEqual({item["path"] for item in tree["tree"]}, {
            "cases/immobilienkaufvertrag/ontology.ttl",
            "cases/immobilienkaufvertrag/README.md",
        })
        self.assertEqual(result["expected_ref"], "new-commit")
        self.assertEqual(model_refs, ["parent", "new-commit"])
        self.assertTrue(result["changed"])

    def test_stale_branch_cannot_save(self):
        store = GitHubStore("notariat8", "ontology", "fake-token")
        model = load_case("immobilienkaufvertrag")
        model["expected_ref"] = "old"
        with patch.object(store, "ref", return_value="new"):
            with self.assertRaisesRegex(ValueError, "inzwischen geändert"):
                store.save("immobilienkaufvertrag", "codex/ontology-editor-test", model)

    def test_semantic_review_requires_notary_and_current_commit(self):
        slug = "immobilienkaufvertrag"
        model = load_case(slug)
        model["nodes"][0]["label"] = "Fachliche Bezeichnung im Prüfentwurf"
        changed_ttl, page, changed = prepare_change(slug, model, model["revision"])
        self.assertTrue(changed)
        original = (ROOT / "cases" / slug / "ontology.ttl").read_text(encoding="utf-8")
        base, head = "a" * 40, "b" * 40
        pr = {
            "number": 42, "title": "Fachliche Änderung: Immobilienkaufvertrag", "state": "open",
            "base": {"ref": "main", "sha": base}, "head": {"sha": head, "repo": {"full_name": "notariat8/ontology"}},
            "changed_files": 2, "draft": False, "user": {"login": "author"},
            "html_url": "https://github.com/notariat8/ontology/pull/42", "body": "Fachlicher Grund und Quelle", "updated_at": "2026-09-28T00:00:00Z",
        }
        store = GitHubStore("notariat8", "ontology", "fake-token")
        reviewed = []

        def request(method, path, payload=None):
            if (method, path) == ("GET", "/pulls?state=open&base=main&per_page=100"):
                return [{"number": 42}]
            if (method, path) == ("GET", "/pulls/42"):
                return pr
            if (method, path) == ("GET", "/pulls/42/files?per_page=100"):
                return [{"filename": f"cases/{slug}/ontology.ttl"}, {"filename": f"cases/{slug}/README.md"}]
            if (method, path) == ("GET", f"/compare/{base}...{head}"):
                return {"merge_base_commit": {"sha": base}}
            if method == "GET" and path.startswith(f"/contents/cases/{slug}/"):
                file, ref = path.split("?ref=")
                content = original if ref == base else changed_ttl if file.endswith("ontology.ttl") else page
                return {"encoding": "base64", "content": base64.b64encode(content.encode()).decode()}
            if (method, path) == ("POST", "/pulls/42/reviews"):
                reviewed.append(payload)
                return {"html_url": "https://github.com/notariat8/ontology/pull/42#pullrequestreview-1"}
            raise AssertionError((method, path))

        with patch.object(store, "request", side_effect=request), patch.object(store, "model_root", return_value=nullcontext(ROOT)):
            self.assertEqual(store.list_case_reviews()[0]["case"], slug)
            detail = store.review_detail(42)
            self.assertEqual(detail["problem"], "")
            self.assertTrue(any("Fachliche Bezeichnung im Prüfentwurf" in item for item in detail["changes"]))
            with self.assertRaisesRegex(PermissionError, "Notarkonten"):
                store.submit_case_review(42, head, "APPROVE", "Fachlich ausführlich geprüft", "reviewer", set())
            with self.assertRaisesRegex(ValueError, "neuen Stand"):
                store.submit_case_review(42, base, "APPROVE", "Fachlich ausführlich geprüft", "notary", {"notary"})
            with self.assertRaisesRegex(ValueError, "nicht selbst"):
                store.submit_case_review(42, head, "APPROVE", "Fachlich ausführlich geprüft", "author", {"author"})
            with self.assertRaisesRegex(ValueError, "als geprüft bestätigt"):
                store.submit_case_review(42, head, "APPROVE", "Fachlich ausführlich geprüft", "notary", {"notary"})
            url = store.submit_case_review(42, head, "APPROVE", "Fachlich ausführlich geprüft", "notary", {"notary"}, {"terms": True, "sources": True, "relations": True})
            changed_ttl += '\n<https://notariat8.github.io/ontology/id/case/immobilienkaufvertrag/node/property.identity> <https://example.org/unmodeled> "Zusatz" .\n'
            self.assertIn("Zusätzliche RDF-Änderungen", store.review_detail(42)["problem"])
            with self.assertRaisesRegex(ValueError, "nicht fachlich freigabefähig"):
                store.submit_case_review(42, head, "APPROVE", "Fachlich ausführlich geprüft", "notary", {"notary"}, {"terms": True, "sources": True, "relations": True})
            store.submit_case_review(42, head, "REQUEST_CHANGES", "Bitte zusätzliche RDF-Aussage erläutern", "specialist", set())
        self.assertIn("pullrequestreview", url)
        self.assertEqual(reviewed[0]["commit_id"], head)
        self.assertEqual(reviewed[0]["event"], "APPROVE")
        self.assertIn("Fachlich geprüft", reviewed[0]["body"])
        self.assertEqual(reviewed[1]["event"], "REQUEST_CHANGES")


if __name__ == "__main__":
    unittest.main()
