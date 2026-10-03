# SPDX-License-Identifier: AGPL-3.0-or-later
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from build_learning import ROOT, outputs

class LearningTests(unittest.TestCase):
    def test_published_handbook_and_course_match_maintained_sources(self):
        for path, expected in outputs().items():
            with self.subTest(path=path):
                self.assertEqual((ROOT / path).read_text(encoding='utf-8'), expected)
