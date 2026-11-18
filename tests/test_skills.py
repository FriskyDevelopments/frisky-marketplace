from pathlib import Path
import tempfile
import unittest

from scripts.marketplace import ROOT, manifest_paths, read_json, validate_skills


class SkillTests(unittest.TestCase):
    def test_declared_skills_and_links_exist(self):
        for path in manifest_paths():
            with self.subTest(plugin=str(path.relative_to(ROOT))):
                validate_skills(read_json(path), path.parent)

    def test_missing_empty_or_incomplete_skills_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = {"skills": "./skills/"}
            with self.assertRaisesRegex(ValueError, "directory is missing"):
                validate_skills(manifest, root)
            (root / "skills").mkdir()
            with self.assertRaisesRegex(ValueError, "has no skills"):
                validate_skills(manifest, root)
            (root / "skills/demo").mkdir()
            for content in (None, "", "   \n"):
                if content is not None:
                    (root / "skills/demo/SKILL.md").write_text(content, encoding="utf-8")
                with self.subTest(content=content), self.assertRaisesRegex(ValueError, "nonempty SKILL.md"):
                    validate_skills(manifest, root)

    def test_session_start_must_resolve_to_a_skill(self):
        manifest = read_json(ROOT / "framer/kimi.plugin.json")
        validate_skills(manifest, ROOT / "framer")
        manifest["sessionStart"]["skill"] = "missing"
        with self.assertRaisesRegex(ValueError, "missing skill"):
            validate_skills(manifest, ROOT / "framer")
        with self.assertRaises(ValueError):
            validate_skills({"sessionStart": {"skill": "demo"}}, ROOT)

    def test_local_links_images_and_reference_links_require_targets(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill = root / "skills/demo/SKILL.md"
            skill.parent.mkdir(parents=True)
            (skill.parent / "present file.md").write_text("# Present", encoding="utf-8")
            manifest = {"skills": "./skills/", "sessionStart": {"skill": "demo"}}
            skill.write_text('[doc](present%20file.md#heading)\n[remote](https://example.com)\n[anchor](#heading)', encoding="utf-8")
            validate_skills(manifest, root)
            for content in (
                "[doc](missing.md)", "![image](missing.png)",
                "[doc][ref]\n[ref]: missing.md", "[doc](<missing file.md>)",
                "[escape](../../../outside.md)", "[absolute](/missing.md)",
            ):
                skill.write_text(content, encoding="utf-8")
                with self.subTest(content=content), self.assertRaises(ValueError):
                    validate_skills(manifest, root)

    def test_skill_directory_cannot_escape_plugin_root(self):
        with self.assertRaises(ValueError):
            validate_skills({"skills": "../skills"}, ROOT / "framer")
