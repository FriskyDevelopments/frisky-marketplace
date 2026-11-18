import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def local_path(root, value):
    if not isinstance(value, str) or not value or Path(value).is_absolute():
        raise ValueError("Expected a nonempty relative path")
    root = root.resolve()
    path = (root / value).resolve()
    if not path.is_relative_to(root):
        raise ValueError("Local path escapes its root")
    return path


def validate_index_paths(index, root=ROOT):
    for entry in index["plugins"]:
        if "path" not in entry:
            continue
        path = local_path(root, entry["path"])
        if not path.is_dir():
            raise ValueError("Indexed plugin directory is missing")
        if not (path / "kimi.plugin.json").is_file():
            raise ValueError("Indexed plugin manifest is missing")


def manifest_paths(root=ROOT):
    return sorted(
        path for path in root.rglob("kimi.plugin.json")
        if not any(part.startswith(".") for part in path.relative_to(root).parts)
    )


def validate_schema(value, filename, label):
    schema = read_json(ROOT / "schemas" / filename)
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = list(validator.iter_errors(value))
    if errors:
        # Do not echo manifest values, which may contain connection configuration.
        locations = ["/".join(map(str, error.absolute_path)) or "<root>" for error in errors]
        raise ValueError(f"Invalid {label} fields: " + ", ".join(locations))


def validate_manifest(manifest):
    validate_schema(manifest, "plugin-manifest.schema.json", "manifest")


def validate_index(index, root=ROOT):
    validate_schema(index, "marketplace-index.schema.json", "index")
    validate_index_paths(index, root)
    names = set()
    paths = set()
    for entry in index["plugins"]:
        if entry["name"] in names:
            raise ValueError("Duplicate indexed plugin name")
        names.add(entry["name"])
        if "path" in entry:
            path = local_path(root, entry["path"])
            if path in paths:
                raise ValueError("Duplicate indexed plugin path")
            paths.add(path)
            manifest = read_json(path / "kimi.plugin.json")
            if manifest.get("name") != entry["name"]:
                raise ValueError("Index and manifest plugin names differ")


def validate_skills(manifest, plugin_root):
    skills = {}
    if "skills" in manifest:
        directory = local_path(plugin_root, manifest["skills"])
        if not directory.is_dir():
            raise ValueError("Declared skills directory is missing")
        for child in sorted(directory.iterdir()):
            if child.name.startswith(".") or not child.is_dir():
                continue
            skill = local_path(plugin_root, str(child.relative_to(plugin_root))) / "SKILL.md"
            skill = local_path(plugin_root, str(skill.relative_to(plugin_root)))
            if not skill.is_file() or not skill.read_text(encoding="utf-8").strip():
                raise ValueError("Skill must have a nonempty SKILL.md")
            skills[child.name] = skill
        if not skills:
            raise ValueError("Declared skills directory has no skills")
    if "sessionStart" in manifest and manifest["sessionStart"]["skill"] not in skills:
        raise ValueError("sessionStart references a missing skill")
    for skill in skills.values():
        text = skill.read_text(encoding="utf-8")
        links = re.findall(r"\[[^\]]*\]\(\s*(<[^>]+>|[^\s)]+)", text)
        links += re.findall(r"^\s*\[[^\]]+\]:\s*(<[^>]+>|\S+)", text, re.MULTILINE)
        for link in links:
            target = urlsplit(link.strip("<>"))
            if target.scheme or target.netloc or not target.path:
                continue
            path = local_path(plugin_root, str(skill.parent.relative_to(plugin_root) / unquote(target.path)))
            if not path.exists():
                raise ValueError("Skill has a missing local link target")
