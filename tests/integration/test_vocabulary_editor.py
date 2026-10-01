# SPDX-License-Identifier: AGPL-3.0-or-later
"""Semantic and layout checks for maintained core Turtle."""

from pathlib import Path
import sys
import unittest

from rdflib import Graph
from rdflib.compare import to_isomorphic

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from case_editor_model import ROOT

from vocabulary_editor import model, prepare_change


CORE = (ROOT / "ontology/core.ttl").read_text(encoding="utf-8")


TERM_COUNT = len(model(CORE)["terms"])

class VocabularyEditorTests(unittest.TestCase):
    def test_roundtrip_and_small_diff(self):
        original = model(CORE)
        self.assertEqual(len(original["terms"]), TERM_COUNT)
        self.assertEqual(prepare_change(CORE, original), (CORE, [], False))
        subject = next(item for item in original["terms"] if item["id"] == "Dokumenttyp")
        subject["comment"] = "Abstrakte Art eines für einen Fall benötigten Dokuments."
        updated, changes, changed = prepare_change(CORE, original)
        self.assertTrue(changed)
        self.assertEqual(len(changes), 1)
        self.assertEqual(updated.count("n8:Dokumenttyp a owl:Class"), 1)
        self.assertEqual(len(updated.splitlines()) - len(CORE.splitlines()), 2)
        self.assertEqual(model(updated)["terms"].__len__(), TERM_COUNT)
        old_graph, new_graph = Graph().parse(data=CORE, format="turtle"), Graph().parse(data=updated, format="turtle")
        self.assertEqual(len(new_graph) - len(old_graph), 1)
        self.assertNotEqual(to_isomorphic(old_graph), to_isomorphic(new_graph))

    def test_new_term_and_guards(self):
        proposed = model(CORE)
        proposed["terms"].append({
            "id": "Fristenart", "kind": "class", "label": "Fristenart", "comment": "Abstrakte Art einer zu prüfenden Frist.",
            "parent": "n8:Fallbaustein", "domain": "", "range": "",
        })
        updated, changes, changed = prepare_change(CORE, proposed)
        self.assertTrue(changed)
        self.assertEqual(len(model(updated)["terms"]), TERM_COUNT + 1)
        self.assertTrue(any("Oberklasse" in change for change in changes))
        with self.assertRaisesRegex(ValueError, "inzwischen geändert"):
            prepare_change(updated, proposed)
        proposed["terms"][-1]["parent"] = "n8:Fristenart"
        with self.assertRaisesRegex(ValueError, "Kreis"):
            prepare_change(CORE, proposed)
        proposed["terms"].pop()
        proposed["terms"] = [item for item in proposed["terms"] if item["id"] != "Dokumenttyp"]
        with self.assertRaisesRegex(ValueError, "nicht entfernt"):
            prepare_change(CORE, proposed)

    def test_every_existing_term_can_be_edited_without_losing_other_triples(self):
        original = model(CORE)
        for identifier in [item["id"] for item in original["terms"]]:
            proposed = model(CORE)
            next(item for item in proposed["terms"] if item["id"] == identifier)["label"] += " Entwurf"
            updated, changes, changed = prepare_change(CORE, proposed)
            self.assertTrue(changed, identifier)
            self.assertEqual(len(changes), 1, identifier)
            self.assertEqual(len(model(updated)["terms"]), len(original["terms"]), identifier)

    def test_multiline_definition_remains_editable(self):
        proposed = model(CORE)
        item = next(item for item in proposed["terms"] if item["id"] == "Dokumenttyp")
        item["comment"] = "Erste Zeile.\nZweite Zeile."
        updated, _, _ = prepare_change(CORE, proposed)
        self.assertIn('Erste Zeile.\\nZweite Zeile.', updated)
        again = model(updated)
        self.assertEqual(next(item for item in again["terms"] if item["id"] == "Dokumenttyp")["comment"], item["comment"])
        next(item for item in again["terms"] if item["id"] == "Dokumenttyp")["comment"] += " Weitere Erläuterung."
        second, _, _ = prepare_change(updated, again)
        self.assertEqual(len(model(second)["terms"]), TERM_COUNT)


if __name__ == "__main__":
    unittest.main()
