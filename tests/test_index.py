import copy
import json
from pathlib import Path
import tempfile
import unittest

from scripts.marketplace import ROOT, read_json, validate_index
from scripts.generate_roster import generate_readme


class IndexCompatibilityTests(unittest.TestCase):
    def test_native_marketplace_index_is_compatible(self):
        index = read_json(ROOT / "plugins.json")
        validate_index(index)
        self.assertEqual(index, json.loads(json.dumps(index, ensure_ascii=False)))

    def test_local_and_external_entries_and_optional_metadata(self):
        index = {
            "name": "fixture",
            "plugins": [
                {"name": "chatprd", "path": "./chatprd"},
                {"name": "remote", "url": "https://example.com/org/plugin", "description": "连接 · español", "category": "DEVTOOLS", "owner": "example"},
            ],
            "futureMetadata": True,
        }
        validate_index(index)
        index["plugins"][1]["category"] = "DEVELOPER_TOOLS"
        validate_index(index)
        validate_index({"name": "empty-marketplace", "plugins": []})

    def test_malformed_indexes_are_rejected(self):
        entry = {"name": "remote", "url": "https://example.com/plugin"}
        invalid = [None, [], {}, {"name": "fixture", "plugins": {}}, {"name": "", "plugins": []}]
        for plugin in (
            {}, {"url": entry["url"]}, {"name": "demo"},
            {**entry, "path": "./demo"}, {**entry, "url": "not-a-url"},
            {**entry, "name": "Bad Name"}, {**entry, "description": 42},
            {**entry, "owner": []}, {"name": "demo", "path": ""},
        ):
            invalid.append({"name": "fixture", "plugins": [plugin]})
        for number, index in enumerate(invalid):
            with self.subTest(case=number), self.assertRaises(ValueError):
                validate_index(index)

    def test_duplicate_names_are_rejected(self):
        entry = {"name": "remote", "url": "https://example.com/plugin"}
        with self.assertRaisesRegex(ValueError, "Duplicate indexed plugin name"):
            validate_index({"name": "fixture", "plugins": [entry, copy.deepcopy(entry)]})

    def test_local_names_and_resolved_paths_are_consistent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "demo").mkdir()
            (root / "demo/kimi.plugin.json").write_text('{"name": "demo"}', encoding="utf-8")
            index = {"name": "fixture", "plugins": [{"name": "different", "path": "./demo"}]}
            with self.assertRaisesRegex(ValueError, "names differ"):
                validate_index(index, root)
            index["plugins"][0]["name"] = "demo"
            validate_index(index, root)
            index["plugins"].append({"name": "alias", "path": "./demo/../demo"})
            with self.assertRaisesRegex(ValueError, "Duplicate indexed plugin path"):
                validate_index(index, root)

    def test_roster_links_support_local_paths_with_spaces(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "demo plugin").mkdir()
            (root / "demo plugin/kimi.plugin.json").write_text(
                '{"name": "demo", "interface": {"displayName": "Demo"}}', encoding="utf-8"
            )
            index = {"name": "fixture", "plugins": [{"name": "demo", "path": "./demo plugin"}]}
            validate_index(index, root)
            text = (ROOT / "README.md").read_text(encoding="utf-8")
            self.assertIn("[**demo**](./demo%20plugin)", generate_readme(text, index, root))
