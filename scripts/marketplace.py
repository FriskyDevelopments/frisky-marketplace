import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


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
