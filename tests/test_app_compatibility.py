import json
import unittest

from scripts.app_compatibility import END, ROOT, START, render_table


class AppCompatibilityTests(unittest.TestCase):
    def setUp(self):
        self.index = {"plugins": [{"name": "example"}]}

    def test_verified_versions_are_visible(self):
        table = render_table(self.index, {"example": ["1.2.3", "2.0.0-beta.1"]})
        self.assertIn("| `example` | `1.2.3`, `2.0.0-beta.1` |", table)

    def test_unknown_is_not_unrestricted_support(self):
        self.assertIn("| `example` | Not yet verified |",
                      render_table(self.index, {"example": None}))

    def test_missing_and_obsolete_plugins_are_rejected(self):
        for metadata in ({}, {"example": None, "removed": None}):
            with self.subTest(metadata=metadata), self.assertRaises(ValueError):
                render_table(self.index, metadata)

    def test_invalid_version_lists_are_rejected(self):
        for value in ([], "1.2.3", [""], [1], [None], ["1.0.0", "1.0.0"],
                      ["1.0.0 | anything"], ["<script>"]):
            with self.subTest(value=value), self.assertRaises(ValueError):
                render_table(self.index, {"example": value})

    def test_readme_matches_metadata_for_every_plugin(self):
        table = render_table(json.loads((ROOT / "plugins.json").read_text()),
                             json.loads((ROOT / "app-compatibility.json").read_text()))
        readme = (ROOT / "README.md").read_text()
        self.assertEqual(readme.count(START), 1)
        self.assertEqual(readme.count(END), 1)
        self.assertIn(table, readme)


if __name__ == "__main__":
    unittest.main()
