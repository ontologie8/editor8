# SPDX-License-Identifier: AGPL-3.0-or-later
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from rdflib import Graph, Literal, RDF, RDFS
from rdflib.compare import graph_diff, to_isomorphic
from fixtures import DemoDataset
from case_editor import preview_change
from case_editor_model import N8, SKOS, load_case, node_uri, prepare_change
from graph_comparison import case_comparison, vocabulary_comparison


class GraphComparisonTests(unittest.TestCase):
    def setUp(self):
        self.demo = DemoDataset()
        self.addCleanup(self.demo.close)

    def test_preview_counts_are_the_actual_saved_rdf_delta(self):
        model = load_case("demo-eins", self.demo.root)
        model["nodes"][0]["label"] = "Geänderte künstliche Frage"
        model["edges"].append({"from": "demo0", "type": "informiert", "to": "demo2"})
        result = preview_change("demo-eins", model, self.demo.root)
        ttl, _, _ = prepare_change("demo-eins", model, model["revision"], self.demo.root)
        original = Graph().parse(self.demo.root / "cases/demo-eins/ontology.ttl", format="turtle")
        _, added, removed = graph_diff(to_isomorphic(original), to_isomorphic(Graph().parse(data=ttl, format="turtle")))
        diff = result["comparison"]
        self.assertEqual((diff["rdf_added"], diff["rdf_removed"]), (len(added), len(removed)))
        self.assertEqual(diff["node_changes"], {"added": 0, "removed": 0, "changed": 1})
        self.assertEqual(diff["edge_changes"], {"added": 1, "removed": 0})
        self.assertEqual({node["id"] for node in diff["after"]["nodes"]}, {"demo0", "demo1", "demo2"})

    def test_removed_nodes_edges_and_isolated_additions_remain_visible(self):
        path = self.demo.root / "cases/demo-eins/ontology.ttl"
        before = Graph().parse(path, format="turtle")
        case = N8["vorgangsart-demo-eins"]
        extra = node_uri("demo-eins", "local.extra")
        before.add((case, N8.hatBaustein, extra))
        before.add((extra, RDF.type, N8.Dokumenttyp))
        before.add((extra, N8.lokaleNodeId, Literal("local.extra")))
        before.add((extra, SKOS.prefLabel, Literal("Künstliches Zusatzdokument", lang="de")))
        before.add((node_uri("demo-eins", "demo0"), N8.erfordert, extra))
        after = Graph()
        after += before
        after.remove((extra, None, None)); after.remove((None, None, extra))
        diff = case_comparison("demo-eins", before.serialize(format="turtle"), after.serialize(format="turtle"))
        self.assertEqual(diff["node_changes"]["removed"], 1)
        self.assertEqual(diff["edge_changes"]["removed"], 1)
        self.assertIn("local.extra", {node["id"] for node in diff["before"]["nodes"]})
        self.assertNotIn("local.extra", {node["id"] for node in diff["after"]["nodes"]})
        reverse = case_comparison("demo-eins", after.serialize(format="turtle"), before.serialize(format="turtle"))
        self.assertEqual(reverse["node_changes"]["added"], 1)

    def test_turtle_formatting_and_metadata_only_do_not_invent_node_effects(self):
        text = (self.demo.root / "cases/demo-eins/ontology.ttl").read_text(encoding="utf-8")
        diff = case_comparison("demo-eins", text, Graph().parse(data=text, format="turtle").serialize(format="turtle"))
        self.assertEqual(diff["rdf_added"], 0); self.assertEqual(diff["rdf_removed"], 0)
        self.assertEqual(diff["affected_nodes"], [])
        model = load_case("demo-eins", self.demo.root); model["summary"] = "Nur die Beschreibung geändert"
        diff = preview_change("demo-eins", model, self.demo.root)["comparison"]
        self.assertEqual(diff["node_changes"]["changed"], 0)
        self.assertEqual(diff["after"]["nodes"], [])
        self.assertGreater(diff["rdf_added"], 0)

    def test_shared_vocabulary_comparison_uses_real_class_labels(self):
        text = (self.demo.root / "ontology/core.ttl").read_text(encoding="utf-8")
        graph = Graph().parse(data=text, format="turtle")
        graph.set((N8.Dokumenttyp, RDFS.label, Literal("Künstliche Dokumentklasse", lang="de")))
        diff = vocabulary_comparison(text, graph.serialize(format="turtle"))
        self.assertEqual(diff["node_changes"]["changed"], 1)
        self.assertEqual(diff["after"]["nodes"][0]["id"], "Dokumenttyp")
        self.assertEqual(diff["after"]["nodes"][0]["label"], "Künstliche Dokumentklasse")
