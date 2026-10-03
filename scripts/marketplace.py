import json
from pathlib import Path

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


def validate_manifest(manifest):
    schema = read_json(ROOT / "schemas/plugin-manifest.schema.json")
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = list(validator.iter_errors(manifest))
    if errors:
        # Do not echo manifest values, which may contain connection configuration.
        locations = ["/".join(map(str, error.absolute_path)) or "<root>" for error in errors]
        raise ValueError("Invalid manifest fields: " + ", ".join(locations))
