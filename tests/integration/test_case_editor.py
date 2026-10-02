# SPDX-License-Identifier: AGPL-3.0-or-later
"""Regression checks for preserving RDF while editing through the browser model."""

import sys
import http.client
from pathlib import Path
import json
from difflib import SequenceMatcher
import shutil
import tempfile
import threading
import unittest
from unittest.mock import patch

from rdflib import Graph, Literal, URIRef
from rdflib.compare import to_isomorphic

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from case_editor_model import DCT, N8, RDFS, ROOT, case_uri, graph_from_model, load_case, prepare_change, slugs
import case_editor
import case_editor_model
import case_document as render_case_docs
sys.path.append(str(ROOT / "scripts"))
import validate_cases


SLUG = "immobilienkaufvertrag"


class CaseEditorTests(unittest.TestCase):
    def setUp(self):
        self.model = load_case(SLUG)
        self.original = Graph().parse(ROOT / "cases" / SLUG / "ontology.ttl", format="turtle")

    def test_vocabulary_branch_cannot_write_case(self):
        with patch.object(case_editor, "git_branch", return_value="codex/ontology-vocabulary-20260928-120000"):
            with self.assertRaisesRegex(ValueError, "getrennte Arbeitszweige"):
                case_editor.write_change(SLUG, self.model)

    def test_unchanged_form_is_semantically_identical_and_does_not_rewrite(self):
        candidate = graph_from_model(SLUG, self.model, self.original)
        self.assertEqual(to_isomorphic(candidate), to_isomorphic(self.original))
        ttl, page, changed = prepare_change(SLUG, self.model, self.model["revision"])
        self.assertFalse(changed)
        self.assertEqual(ttl, (ROOT / "cases" / SLUG / "ontology.ttl").read_text(encoding="utf-8"))
        self.assertIn("flowchart LR", page)

    def test_all_20_cases_roundtrip_without_semantic_loss(self):
        self.assertEqual(len(slugs()), 20)
        for slug in slugs():
            with self.subTest(case=slug):
                original = Graph().parse(ROOT / "cases" / slug / "ontology.ttl", format="turtle")
                model = load_case(slug)
                self.assertTrue(model["bpmn_source"].startswith("https://github.com/notariat8/NaC/blob/"))
                self.assertEqual(to_isomorphic(graph_from_model(slug, model, original)), to_isomorphic(original))
                _, _, changed = prepare_change(slug, model, model["revision"])
                self.assertFalse(changed)

    def test_small_change_stays_small_in_all_20_turtle_files(self):
        for slug in slugs():
            with self.subTest(case=slug):
                model = load_case(slug)
                source = (ROOT / "cases" / slug / "ontology.ttl").read_text(encoding="utf-8")
                model["nodes"][0]["label"] += " (redaktioneller Entwurf)"
                ttl, _, changed = prepare_change(slug, model, model["revision"])
                self.assertTrue(changed)
                self.assertGreater(SequenceMatcher(None, source.splitlines(), ttl.splitlines()).ratio(), 0.90)
                self.assertIn("# Beziehungen aus dem NaC-Vorlagengraphen", ttl)

    def test_change_keeps_unknown_triples_and_pinned_source(self):
        extra_predicate = URIRef("https://example.org/custom")
        subject = URIRef(f"{N8}case/{SLUG}/node/property.identity")
        self.original.add((subject, extra_predicate, Literal("untouched")))
        source = self.original.value(case_uri(SLUG), DCT.source)
        self.model["nodes"][0]["label"] = "Geänderter Fachbegriff"
        candidate = graph_from_model(SLUG, self.model, self.original)
        self.assertIn((subject, extra_predicate, Literal("untouched")), candidate)
        self.assertEqual(candidate.value(case_uri(SLUG), DCT.source), source)
        self.assertNotEqual(to_isomorphic(candidate), to_isomorphic(self.original))

    def test_add_local_node_and_relation_without_claiming_nac_origin(self):
        new_node = {
            "id": "local.new-question",
            "category": "required_information",
            "label": "Neue Fachfrage",
            "status": "local-draft",
            "question": "Was ist zu klären?",
            "section": "II",
            "detail": "Fachliche Erläuterung zum Baustein.",
            "owner_role": "notary",
            "privacy_class": "",
            "document_source": "",
            "contains_personal_data": None,
            "required_for": [],
            "options": [],
        }
        self.model["nodes"].append(new_node)
        self.model["edges"].append({"from": new_node["id"], "type": "informiert", "to": "decision.financing_route"})
        candidate = graph_from_model(SLUG, self.model, self.original)
        subject = URIRef(f"{N8}case/{SLUG}/node/local.new-question")
        self.assertEqual(str(candidate.value(subject, N8.lokaleNodeId)), new_node["id"])
        self.assertIsNone(candidate.value(subject, N8.nacNodeId))
        self.assertEqual(str(candidate.value(subject, N8.pflegeStatus)), "local-draft")
        self.assertIsNone(candidate.value(subject, N8.quellstatus))
        self.assertEqual(str(candidate.value(subject, N8.quellabschnitt)), "II")
        self.assertEqual(str(candidate.value(subject, RDFS.comment)), "Fachliche Erläuterung zum Baustein.")
        ttl, page, changed = prepare_change(SLUG, self.model, self.model["revision"])
        self.assertTrue(changed)
        self.assertIn("Neue Fachfrage", page)
        self.assertEqual(to_isomorphic(Graph().parse(data=ttl, format="turtle")), to_isomorphic(candidate))

    def test_rejects_unknown_case_and_stale_revision(self):
        with self.assertRaisesRegex(ValueError, "Unbekannter Fall"):
            load_case("../NaC")
        with self.assertRaisesRegex(ValueError, "inzwischen geändert"):
            prepare_change(SLUG, self.model, "wrong")

    def test_imported_nac_node_cannot_be_deleted(self):
        removed = self.model["nodes"].pop(0)["id"]
        self.model["edges"] = [edge for edge in self.model["edges"] if removed not in (edge["from"], edge["to"])]
        with self.assertRaisesRegex(ValueError, "NaC-Vorlage können nicht entfernt"):
            graph_from_model(SLUG, self.model, self.original)

    def test_preview_describes_validated_change_without_writing(self):
        path = ROOT / "cases" / SLUG / "ontology.ttl"
        before = path.read_bytes()
        self.assertFalse(case_editor.preview_change(SLUG, self.model)["changed"])
        self.model["nodes"][0]["label"] = "Neue fachliche Bezeichnung"
        preview = case_editor.preview_change(SLUG, self.model)
        self.assertTrue(preview["changed"])
        self.assertTrue(any("Neue fachliche Bezeichnung" in item and "Bezeichnung" in item for item in preview["changes"]))
        self.assertEqual(path.read_bytes(), before)
        self.model["revision"] = "wrong"
        with self.assertRaisesRegex(ValueError, "inzwischen geändert"):
            case_editor.preview_change(SLUG, self.model)

    def test_review_requires_editor_branch_and_fachliche_begruendung(self):
        with patch.object(case_editor, "git_branch", return_value="main"):
            with self.assertRaisesRegex(ValueError, "Änderung beginnen"):
                case_editor.submit_review(SLUG, {"reason": "Eine ausführliche Begründung", "source": "NaC-Commit abc123"})
        with patch.object(case_editor, "git_branch", return_value="codex/ontology-editor-20260928-120000"):
            with self.assertRaisesRegex(ValueError, "fachlichen Grund"):
                case_editor.submit_review(SLUG, {"reason": "kurz", "source": "NaC-Commit abc123"})

    def test_isolated_model_root_does_not_change_shared_repository(self):
        with tempfile.TemporaryDirectory() as location:
            isolated = Path(location)
            (isolated / "catalog").mkdir()
            (isolated / "cases" / SLUG).mkdir(parents=True)
            for filename in ("nac-baseline.json", "nac-usecases.ttl"):
                shutil.copy2(ROOT / "catalog" / filename, isolated / "catalog" / filename)
            shutil.copy2(ROOT / "cases" / SLUG / "ontology.ttl", isolated / "cases" / SLUG / "ontology.ttl")
            model = load_case(SLUG, isolated)
            model["nodes"][0]["label"] = "Isolierte Änderung"
            ttl, page, changed = prepare_change(SLUG, model, model["revision"], isolated)
            self.assertTrue(changed)
            self.assertIn("Isolierte Änderung", page)
            self.assertIn("Isolierte Änderung", ttl)
            self.assertNotIn("Isolierte Änderung", (ROOT / "cases" / SLUG / "ontology.ttl").read_text(encoding="utf-8"))

    def test_local_editor_serves_case_deep_links(self):
        server = case_editor.EditorServer(("127.0.0.1", 0))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
            connection.request("GET", "/?case=erbausschlagung")
            response = connection.getresponse()
            self.assertEqual(response.status, 200)
            self.assertIn(b"<title>editor8", response.read())
            connection.close()
            connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
            connection.request("GET", "/api/drafts")
            response = connection.getresponse()
            self.assertEqual(response.status, 200)
            self.assertEqual(json.loads(response.read()), [])
            connection.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)

    def test_rejects_real_case_values_and_dangling_edges(self):
        self.model["nodes"][0]["value"] = "private data"
        # The editable schema ignores extra fields rather than writing them to RDF.
        candidate = graph_from_model(SLUG, self.model, self.original)
        self.assertFalse(any(str(predicate).endswith("/value") for _, predicate, _ in candidate))
        self.model["edges"][0]["to"] = "missing.node"
        with self.assertRaisesRegex(ValueError, "Ungültige oder doppelte Beziehung"):
            graph_from_model(SLUG, self.model, self.original)

    def test_save_writes_turtle_and_matching_mermaid_in_isolated_copy(self):
        with tempfile.TemporaryDirectory() as location:
            copy_root = Path(location)
            (copy_root / "catalog").mkdir()
            (copy_root / "cases" / SLUG).mkdir(parents=True)
            shutil.copy2(ROOT / "catalog/nac-baseline.json", copy_root / "catalog/nac-baseline.json")
            shutil.copy2(ROOT / "catalog/nac-usecases.ttl", copy_root / "catalog/nac-usecases.ttl")
            shutil.copy2(ROOT / "cases" / SLUG / "ontology.ttl", copy_root / "cases" / SLUG / "ontology.ttl")
            shutil.copy2(ROOT / "cases" / SLUG / "README.md", copy_root / "cases" / SLUG / "README.md")
            with (
                patch.object(case_editor_model, "ROOT", copy_root),
                patch.object(render_case_docs, "ROOT", copy_root),
                patch.object(validate_cases, "ROOT", copy_root),
                patch.dict(validate_cases.render.__globals__, {'ROOT': copy_root}),
                patch.object(case_editor, "git_branch", return_value="codex/test"),
            ):
                model = load_case(SLUG)
                model["nodes"][0]["label"] = "Fachlich geänderter Begriff"
                result = case_editor.write_change(SLUG, model)
                self.assertTrue(result["changed"])
                self.assertIn("Fachlich geänderter Begriff", (copy_root / "cases" / SLUG / "README.md").read_text(encoding="utf-8"))
                self.assertEqual(
                    render_case_docs.render(SLUG),
                    (copy_root / "cases" / SLUG / "README.md").read_text(encoding="utf-8"),
                )
                self.assertEqual(
                    result["revision"],
                    case_editor_model.revision(copy_root / "cases" / SLUG / "ontology.ttl"),
                )
                ref = json.loads((copy_root / "catalog/nac-baseline.json").read_text(encoding="utf-8"))["source_ref"]
                self.assertEqual(validate_cases.check_one(SLUG, ref, None), (22, 8))
                amended = load_case(SLUG)
                amended["nodes"].append({
                    "id": "local.review-question", "category": "required_information",
                    "label": "Zusätzliche Fachfrage", "status": "local-draft",
                    "question": "", "owner_role": "", "privacy_class": "",
                    "document_source": "", "contains_personal_data": None,
                    "required_for": [], "options": [],
                })
                amended["edges"].append({"from": "local.review-question", "type": "informiert", "to": "decision.financing_route"})
                case_editor.write_change(SLUG, amended)
                self.assertEqual(validate_cases.check_one(SLUG, ref, None), (23, 9))


if __name__ == "__main__":
    unittest.main()
