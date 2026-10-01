# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check the cross-case vocabulary view against the pinned Turtle catalog."""

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from case_editor_model import ROOT, slugs
from vocabulary_impact import impact_index


def source_files():
    read = lambda path: path.read_text(encoding="utf-8")
    return read(ROOT / "ontology/core.ttl"), read(ROOT / "catalog/nac-usecases.ttl"), {
        slug: read(ROOT / "cases" / slug / "ontology.ttl") for slug in slugs()
    }


class VocabularyImpactTests(unittest.TestCase):
    def test_usage_counts_cover_all_20_cases(self):
        core, catalog, cases = source_files()
        result = impact_index(core, catalog, cases, "a" * 40)
        self.assertEqual(result["source_ref"], "a" * 40)
        self.assertEqual(result["case_count"], 20)
        self.assertEqual(sum(item["count"] for item in result["terms"]["Angabenfrage"]), 160)
        self.assertEqual(sum(item["count"] for item in result["terms"]["hatBaustein"]), 392)
        self.assertEqual(len(result["terms"]["hatBpmnModell"]), 20)
        self.assertEqual(result["terms"]["Vorgangsart"][0]["count"], 1)
        self.assertEqual({item["slug"] for item in result["terms"]["hatBaustein"]}, set(slugs()))

    def test_incomplete_case_snapshot_is_rejected(self):
        core, catalog, cases = source_files()
        cases.pop(slugs()[0])
        with self.assertRaisesRegex(ValueError, "vollständigen Datenkatalog"):
            impact_index(core, catalog, cases, "local")


if __name__ == "__main__":
    unittest.main()
