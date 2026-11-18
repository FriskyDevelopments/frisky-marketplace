import unittest

from scripts.generate_roster import generate_readme
from scripts.marketplace import ROOT, read_json


class RosterTests(unittest.TestCase):
    def test_readme_roster_and_count_are_current(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertEqual(text, generate_readme(text, read_json(ROOT / "plugins.json")))

    def test_generation_is_idempotent_and_preserves_manual_content(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        index = {"name": "fixture", "plugins": [{"name": "external", "url": "https://example.com/repo", "description": "A | B\nC"}]}
        generated = generate_readme(text, index)
        self.assertEqual(generated, generate_readme(generated, index))
        self.assertIn("plugins-1-", generated)
        self.assertIn("**1 connectors", generated)
        self.assertIn("[**external**](https://example.com/repo)", generated)
        self.assertIn("A &#124; B C", generated)
        self.assertEqual(text.split("## Install")[1], generated.split("## Install")[1])

    def test_missing_generation_markers_fail(self):
        with self.assertRaises(ValueError):
            generate_readme("manual README", {"name": "fixture", "plugins": []})
