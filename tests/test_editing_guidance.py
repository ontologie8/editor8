# SPDX-License-Identifier: AGPL-3.0-or-later
from contextlib import nullcontext
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from editing_guidance import profile
from fixtures import DemoDataset
from github_store import GitHubStore

CORE = '''@prefix n8: <https://notariat8.github.io/ontology/id/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
n8:Angabenfrage skos:prefLabel "Testfrage"@de ; rdfs:comment "Erklärung des Testtyps"@de .
n8:Dokumenttyp skos:prefLabel "Testdokument"@de .
n8:Nachweistyp skos:prefLabel "Testnachweis"@de .
n8:offeneFrage rdfs:comment "Eigene Erläuterung des Testfelds"@de, "Foreign description"@en .
n8:erfordert rdfs:comment "Testverbindung"@de ; rdfs:domain n8:Angabenfrage ; rdfs:range n8:Dokumenttyp, n8:Nachweistyp .'''


class GuidanceTests(unittest.TestCase):
    def test_missing_metadata_is_explicit_and_does_not_invent_ranges(self):
        result = profile()
        self.assertFalse(result["available"])
        self.assertIsNone(result["revision"])
        self.assertEqual(result["relations"]["erfordert"]["range"], [])
        self.assertIn("keine technischen Rechte", result["fields"]["owner_role"]["description"])

    def test_labels_descriptions_and_multiple_ranges_are_preserved_as_hints(self):
        result = profile(CORE)
        self.assertEqual(result["fields"]["question"]["description"], "Eigene Erläuterung des Testfelds")
        self.assertEqual(result["types"]["required_information"]["description"], "Erklärung des Testtyps")
        relation = result["relations"]["erfordert"]
        self.assertEqual(relation["description"], "Testverbindung")
        self.assertEqual({item["label"] for item in relation["range"]}, {"Testdokument", "Testnachweis"})
        self.assertNotIn("allowed", relation)

    def test_markup_remains_a_plain_text_value(self):
        result = profile(CORE.replace("Testverbindung", "<script>synthetisch</script>"))
        self.assertEqual(result["relations"]["erfordert"]["description"], "<script>synthetisch</script>")

    def test_case_and_vocabulary_use_one_immutable_commit(self):
        dataset = DemoDataset()
        self.addCleanup(dataset.close)
        store = GitHubStore("example", "models", "synthetic-token")
        head = "a" * 40
        with patch.object(store, "ref", return_value=head) as ref, \
             patch.object(store, "model_root", return_value=nullcontext(dataset.root)), \
             patch.object(store, "read_file", return_value=CORE) as read:
            result = store.load_case("demo-eins", "main")
        ref.assert_called_once_with("main")
        read.assert_called_once_with("ontology/core.ttl", head)
        self.assertEqual(result["editing_profile"]["source_ref"], result["expected_ref"])
        self.assertEqual(result["editing_profile"]["fields"]["question"]["description"], "Eigene Erläuterung des Testfelds")
