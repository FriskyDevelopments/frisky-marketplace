#!/usr/bin/env python3
"""Validate the plugin permissions documentation for frisky-marketplace.

Checks, from the repo contents only (no network, no execution of plugins):

1. Every plugin listed in ``plugins.json`` has a section in ``PERMISSIONS.md``.
2. Every plugin directory with a ``kimi.plugin.json`` is also documented.
3. No ``kimi.plugin.json`` manifest carries a non-empty secret-like value
   (API keys, tokens, passwords, bearer secrets). Empty-string placeholders
   are allowed; populated ones fail the check.

Exit code 0 = all good, 1 = problems found. Prints a human-readable report.

Usage:
    python3 scripts/check_permissions.py [repo_root]
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


# Env/manifest keys whose *populated* value would be a committed secret.
SECRET_KEY_PATTERN = re.compile(
    r"(api[_-]?key|secret|token|password|passwd|bearer|client[_-]?secret|"
    r"access[_-]?key|private[_-]?key|credential)",
    re.IGNORECASE,
)

# Values that are obviously placeholders rather than real secrets.
PLACEHOLDER_VALUES = {"", "<key>", "<token>", "<api_key>", "<...>", "changeme"}


def find_secret_values(obj, path="") -> list[str]:
    """Recursively find populated secret-like key/value pairs in a manifest."""
    findings: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            here = f"{path}.{key}" if path else key
            if (
                isinstance(value, str)
                and SECRET_KEY_PATTERN.search(key)
                and value.strip() not in PLACEHOLDER_VALUES
            ):
                findings.append(here)
            findings.extend(find_secret_values(value, here))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            findings.extend(find_secret_values(item, f"{path}[{i}]"))
    return findings


def main(argv: list[str]) -> int:
    repo_root = Path(argv[1]) if len(argv) > 1 else Path(__file__).resolve().parent.parent
    repo_root = repo_root.resolve()

    index_path = repo_root / "plugins.json"
    perms_path = repo_root / "PERMISSIONS.md"

    problems: list[str] = []

    if not index_path.is_file():
        print(f"ERROR: {index_path} not found")
        return 1
    if not perms_path.is_file():
        print(f"ERROR: {perms_path} not found")
        return 1

    index = json.loads(index_path.read_text(encoding="utf-8"))
    perms_text = perms_path.read_text(encoding="utf-8")

    indexed_names = {p["name"] for p in index.get("plugins", [])}

    # Plugin directories that actually ship a manifest.
    manifest_dirs = {
        p.parent.name for p in repo_root.glob("*/kimi.plugin.json")
    }

    all_plugins = sorted(indexed_names | manifest_dirs)

    # 1 & 2: every plugin is documented in PERMISSIONS.md.
    for name in all_plugins:
        # Match a doc heading that references the plugin name, e.g.
        # "### 01 · sentry-connector" or any line containing the name as a token.
        if not re.search(rf"\b{re.escape(name)}\b", perms_text):
            problems.append(f"PERMISSIONS.md is missing a section for '{name}'")

    # Cross-check: indexed vs manifest-present.
    for name in sorted(indexed_names - manifest_dirs):
        # folios ships no mcpServers but may still have a manifest; only warn
        # if the directory has no manifest at all.
        if not (repo_root / name / "kimi.plugin.json").is_file():
            problems.append(
                f"'{name}' is in plugins.json but has no kimi.plugin.json manifest"
            )

    # 3: no committed secrets in any manifest.
    for manifest in sorted(repo_root.glob("*/kimi.plugin.json")):
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            problems.append(f"{manifest.relative_to(repo_root)}: invalid JSON ({exc})")
            continue
        for finding in find_secret_values(data):
            problems.append(
                f"{manifest.relative_to(repo_root)}: populated secret-like field "
                f"'{finding}' (should be empty/placeholder in-repo)"
            )

    # Report.
    print(f"Checked {len(all_plugins)} plugins against PERMISSIONS.md:")
    for name in all_plugins:
        print(f"  - {name}")
    print()

    if problems:
        print(f"FAIL: {len(problems)} problem(s) found:")
        for p in problems:
            print(f"  ! {p}")
        return 1

    print("OK: all plugins documented; no committed secrets found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
