# SPDX-License-Identifier: AGPL-3.0-or-later
"""Historical versions may only become exact, reviewable case proposals."""

from contextlib import nullcontext
from pathlib import Path
import shutil
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from rdflib import Graph
from rdflib.compare import to_isomorphic

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from case_editor import describe_changes, restore_local_case
from case_editor_model import ROOT, load_case, prepare_change
from case_restore import prepare_historical_case
from github_store import GitHubStore


class CaseRestoreTests(unittest.TestCase):
    def setUp(self):
        self.slug = "immobilienkaufvertrag"
        self.original = (ROOT / "cases" / self.slug / "ontology.ttl").read_text(encoding="utf-8")
        model = load_case(self.slug)
        model["nodes"][0]["label"] = "Spätere fachliche Bezeichnung"
        self.current, _, changed = prepare_change(self.slug, model, model["revision"])
        self.assertTrue(changed)
        self.temporary = TemporaryDirectory(prefix="nac-restore-test-")
        self.root = Path(self.temporary.name)
        (self.root / "catalog").mkdir()
        (self.root / "cases" / self.slug).mkdir(parents=True)
        for name in ("nac-baseline.json", "nac-usecases.ttl"):
            shutil.copy2(ROOT / "catalog" / name, self.root / "catalog" / name)
        (self.root / "cases" / self.slug / "ontology.ttl").write_text(self.current, encoding="utf-8")

    def tearDown(self):
        self.temporary.cleanup()

    def test_historical_form_roundtrips_exact_rdf(self):
        proposal = prepare_historical_case(self.slug, self.original, self.root, describe_changes)
        self.assertTrue(proposal["changed"])
        self.assertTrue(any("Spätere fachliche Bezeichnung" in change for change in proposal["changes"]))
        self.assertEqual(to_isomorphic(Graph().parse(data=proposal["turtle"], format="turtle")), to_isomorphic(Graph().parse(data=self.original, format="turtle")))
        self.assertIn("mermaid", proposal["page"])

    def test_unrepresented_historical_rdf_cannot_be_silently_restored(self):
        historical = self.original + '\n<https://notariat8.github.io/ontology/id/unmodeled> <https://example.org/extra> "nicht im Editor" .\n'
        with self.assertRaisesRegex(ValueError, "außerhalb der Editorfelder"):
            prepare_historical_case(self.slug, historical, self.root, describe_changes)

    def test_remote_restore_creates_only_a_new_review_branch(self):
        store = GitHubStore("notariat8", "ontology", "fake-token")
        main, target = "a" * 40, "b" * 40
        branch = "codex/ontology-editor-test-restore"
        history = {"main_ref": main, "case": self.slug, "entries": [{"sha": target}]}
        requests = []

        def request(method, path, payload=None):
            requests.append((method, path, payload))
            if (method, path) == ("GET", "/git/commits/" + main):
                return {"tree": {"sha": "old-tree"}}
            if (method, path) == ("POST", "/git/trees"):
                return {"sha": "new-tree"}
            if (method, path) == ("POST", "/git/commits"):
                return {"sha": "new-commit"}
            if (method, path) == ("POST", "/git/refs"):
                return {}
            raise AssertionError((method, path))

        with (patch.object(store, "ref", return_value=main), patch.object(store, "case_history", return_value=history), patch.object(store, "read_file", return_value=self.original), patch.object(store, "model_root", return_value=nullcontext(self.root)), patch.object(store, "request", side_effect=request)):
            preview = store.preview_case_restore(self.slug, target, main)
            self.assertTrue(preview["changed"])
            result = store.restore_case(self.slug, target, main, branch)
            self.assertEqual(result["branch"], branch)
            with self.assertRaisesRegex(ValueError, "nicht in der angezeigten"):
                store.restore_case(self.slug, "c" * 40, main, branch)
        tree = next(payload for method, path, payload in requests if path == "/git/trees")
        self.assertEqual({item["path"] for item in tree["tree"]}, {f"cases/{self.slug}/ontology.ttl", f"cases/{self.slug}/README.md"})
        self.assertEqual(requests[-1][2], {"ref": "refs/heads/" + branch, "sha": "new-commit"})

    def test_local_restore_uses_the_same_checked_proposal(self):
        main, target = "a" * 40, "b" * 40
        history = {"main_ref": main, "case": self.slug, "entries": [{"sha": target}]}
        with (
            patch("case_editor.git_branch", return_value="main"),
            patch("case_editor.local_case_history", return_value=history),
            patch("case_editor.subprocess.check_output", return_value=self.original.encode("utf-8")),
            patch("case_editor.ROOT", self.root),
            patch("case_editor.start_branch", return_value="codex/ontology-editor-test") as branch,
            patch("case_editor.write_change", return_value={"changed": True}) as write,
        ):
            result = restore_local_case(self.slug, {"target_sha": target, "expected_main": main})
            self.assertEqual(result["branch"], "codex/ontology-editor-test")
            branch.assert_called_once_with("case")
            self.assertEqual(write.call_args.args[0], self.slug)
            self.assertEqual(write.call_args.args[1]["revision"], load_case(self.slug, self.root)["revision"])


if __name__ == "__main__":
    unittest.main()
