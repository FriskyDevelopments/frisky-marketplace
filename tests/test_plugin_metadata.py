import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
CATEGORIES = {"DEVELOPER_TOOLS", "PRODUCTIVITY"}


class PluginMetadataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plugins = json.loads((ROOT / "plugins.json").read_text(encoding="utf-8"))["plugins"]
        cls.manifests = {
            plugin["name"]: json.loads(
                (ROOT / plugin["path"] / "kimi.plugin.json").read_text(encoding="utf-8")
            )
            for plugin in cls.plugins
        }

    def test_ids_match_local_paths_and_manifests(self):
        names = [plugin["name"] for plugin in self.plugins]
        self.assertEqual(len(names), len(set(names)))
        for plugin in self.plugins:
            with self.subTest(plugin=plugin["name"]):
                self.assertRegex(plugin["name"], r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
                self.assertEqual(plugin["path"], f"./{plugin['name']}")
                self.assertEqual(self.manifests[plugin["name"]]["name"], plugin["name"])

    def test_categories_are_canonical_and_match(self):
        for plugin in self.plugins:
            with self.subTest(plugin=plugin["name"]):
                self.assertIn(plugin["category"], CATEGORIES)
                self.assertEqual(
                    plugin["category"],
                    self.manifests[plugin["name"]]["interface"]["category"],
                )

    def test_roster_uses_manifest_display_names_and_categories(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        rows = re.findall(
            r"^\| \d+ \|.*?\[\*\*(.*?)\*\*\]\((\./[^)]+)\).*?\| `([^`]+)` \|$",
            readme,
            re.MULTILINE,
        )
        self.assertEqual(len(rows), len(self.plugins))
        roster = {path: (label, category) for label, path, category in rows}
        self.assertEqual(len(roster), len(rows))
        for plugin in self.plugins:
            with self.subTest(plugin=plugin["name"]):
                display_name = self.manifests[plugin["name"]]["interface"]["displayName"]
                self.assertTrue(display_name)
                self.assertEqual(display_name, display_name.strip())
                self.assertEqual(roster[plugin["path"]], (display_name, plugin["category"]))
