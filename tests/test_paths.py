from pathlib import Path
import tempfile
import unittest

from scripts.marketplace import ROOT, read_json, validate_index_paths


class IndexPathTests(unittest.TestCase):
    def test_indexed_plugin_paths_exist(self):
        validate_index_paths(read_json(ROOT / "plugins.json"))

    def test_directory_and_manifest_are_required(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            index = {"plugins": [{"name": "demo", "path": "./demo"}]}
            with self.assertRaisesRegex(ValueError, "directory is missing"):
                validate_index_paths(index, root)
            (root / "demo").mkdir()
            with self.assertRaisesRegex(ValueError, "manifest is missing"):
                validate_index_paths(index, root)
            (root / "demo/kimi.plugin.json").write_text("{}", encoding="utf-8")
            validate_index_paths(index, root)

    def test_external_repositories_do_not_need_local_paths(self):
        validate_index_paths({"plugins": [{"name": "remote", "url": "https://example.com/repo"}]})

    def test_absolute_traversal_and_symlink_escapes_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            root.mkdir()
            (root / "outside").symlink_to(Path(directory), target_is_directory=True)
            for value in (directory, "../missing", "./outside", "", None):
                with self.subTest(path=value), self.assertRaises(ValueError):
                    validate_index_paths({"plugins": [{"path": value}]}, root)
