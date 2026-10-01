# SPDX-License-Identifier: AGPL-3.0-or-later
"""The search index covers only the pinned NaC building blocks."""

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from case_editor_model import ROOT, slugs
from case_index import build_case_index


class CaseIndexTests(unittest.TestCase):
    def test_index_covers_all_pinned_cases_and_nodes(self):
        read = lambda relative: (ROOT / relative).read_text(encoding="utf-8")
        cases = {slug: read(f"cases/{slug}/ontology.ttl") for slug in slugs()}
        result = build_case_index(read("catalog/nac-usecases.ttl"), cases, "pinned")
        self.assertEqual(result["source_ref"], "pinned")
        self.assertEqual(result["case_count"], 20)
        self.assertEqual(len(result["entries"]), 392)
        self.assertEqual({entry["slug"] for entry in result["entries"]}, set(slugs()))
        self.assertTrue(all(entry["label"] and entry["case_title"] for entry in result["entries"]))
        with self.assertRaisesRegex(ValueError, "vollständigen Datenkatalog"):
            build_case_index(read("catalog/nac-usecases.ttl"), dict(list(cases.items())[:-1]), "pinned")


if __name__ == "__main__":
    unittest.main()
