import copy
import unittest

from scripts.marketplace import ROOT, manifest_paths, read_json, validate_manifest


class ManifestTests(unittest.TestCase):
    def test_every_manifest_matches_schema(self):
        paths = manifest_paths()
        self.assertTrue(paths, "No plugin manifests found")
        for path in paths:
            with self.subTest(manifest=str(path.relative_to(ROOT))):
                validate_manifest(read_json(path))

    def test_invalid_fields_are_rejected(self):
        valid = read_json(ROOT / "framer/kimi.plugin.json")
        invalid = [
            {**valid, "version": "not-a-version"},
            {**valid, "name": "Invalid Name"},
            {**valid, "skills": []},
            {**valid, "interface": {"displayName": 42}},
            {**valid, "mcpServers": {"demo": {}}},
            {**valid, "mcpServers": {"demo": {"url": "not-a-url"}}},
            {**valid, "mcpServers": {"demo": {"command": "npx", "args": "demo"}}},
        ]
        missing = copy.deepcopy(valid)
        del missing["name"]
        invalid.append(missing)
        for manifest in invalid:
            with self.subTest(case=invalid.index(manifest)):
                with self.assertRaises(ValueError):
                    validate_manifest(manifest)

    def test_local_versions_and_extensions_remain_supported(self):
        manifest = read_json(ROOT / "framer/kimi.plugin.json")
        manifest["futureExtension"] = {"enabled": True}
        validate_manifest(manifest)
