#!/usr/bin/env python3
"""Scan plugin JSON configs for accidentally committed secrets.

This marketplace ships connectors as JSON manifests (``plugins.json``,
``*/kimi.plugin.json``, ``*/.mcp.json``). None of them are supposed to carry
real credentials: secrets are provided at runtime via OAuth or a
``Authorization: Bearer <key>`` header the user adds themselves. Credential
fields that do appear in-repo (for example ``FRAMER_API_KEY``) are expected to
be empty-string placeholders.

This scanner walks every JSON config, recursively inspects every string value,
and reports any value that looks like a real secret. It is intentionally
conservative so it stays useful in CI without drowning reviewers in noise:

* empty strings and obvious placeholders ("", "<key>", "YOUR_API_KEY", ...)
  are treated as safe;
* a string is flagged when it either (a) sits under a key whose name signals a
  credential *and* carries a non-placeholder value, or (b) matches a
  high-confidence vendor token pattern anywhere.

The script uses only the Python standard library. Exit code 0 means clean,
1 means at least one likely secret was found, 2 means a usage/parse error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterable, Iterator, List, Tuple

# Files we treat as plugin configuration.
CONFIG_GLOBS: Tuple[str, ...] = (
    "plugins.json",
    "*/kimi.plugin.json",
    "*/.mcp.json",
    "*/*.mcp.json",
)

# Directories never worth scanning.
SKIP_DIRS = {".git", "node_modules", "tests"}

# Key names that denote a credential-bearing field. These are matched against
# normalized *segments* of the JSON key (split on separators / camelCase), so
# "apiKey", "api_key" and "API-KEY" all match "apikey", while unrelated words
# such as "author" (segment "author") do NOT match "auth".
SECRET_KEY_HINTS = frozenset(
    {
        "apikey",
        "secret",
        "secrets",
        "token",
        "accesstoken",
        "refreshtoken",
        "password",
        "passwd",
        "pwd",
        "privatekey",
        "clientsecret",
        "accesskey",
        "secretkey",
        "authorization",
        "credential",
        "credentials",
        "bearer",
    }
)

# Multi-word hints to match on the fully-normalized (separators removed) key,
# since segment splitting would break them apart.
SECRET_KEY_COMPOUNDS = (
    "apikey",
    "accesskey",
    "secretkey",
    "privatekey",
    "clientsecret",
    "accesstoken",
    "refreshtoken",
)

# Values that are clearly placeholders rather than real secrets.
PLACEHOLDER_RE = re.compile(
    r"""^\s*(
        |                                   # empty
        <[^>]*>|                            # <key>, <token>, ...
        \{\{?[^}]*\}?\}|                    # {{ env }} / {VAR}
        \$\{?[a-z0-9_]+\}?|                 # $VAR / ${VAR}
        (your[_-]?)?(api[_-]?key|token|secret|password)|
        changeme|placeholder|example|dummy|sample|redacted|xxx+|\.\.\.|none|null
    )\s*$""",
    re.IGNORECASE | re.VERBOSE,
)

# High-confidence vendor token shapes. These are deliberately specific so a
# literal match is almost certainly a real leaked credential, regardless of the
# key it sits under. (These are detection patterns, not real secrets.)
TOKEN_PATTERNS: Tuple[Tuple[str, re.Pattern], ...] = (
    ("aws_access_key_id", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b")),
    ("slack_token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    ("openai_key", re.compile(r"\bsk-[A-Za-z0-9]{20,}\b")),
    ("stripe_key", re.compile(r"\b[rs]k_(?:live|test)_[A-Za-z0-9]{16,}\b")),
    ("google_api_key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("private_key_block", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----")),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\b")),
    ("bearer_inline", re.compile(r"\bBearer\s+[A-Za-z0-9._\-]{20,}\b")),
)

# Generic "looks like a long opaque credential" heuristic, only applied to
# values sitting under a secret-ish key. Requires mixed character classes so we
# don't flag long slugs, descriptions, or URLs.
HIGH_ENTROPY_RE = re.compile(r"^[A-Za-z0-9+/=_\-]{24,}$")


class Finding:
    def __init__(self, path: Path, json_path: str, reason: str, preview: str):
        self.path = path
        self.json_path = json_path
        self.reason = reason
        self.preview = preview

    def __str__(self) -> str:  # pragma: no cover - formatting only
        return f"{self.path}: {self.json_path}: {self.reason} (value: {self.preview})"


def _is_placeholder(value: str) -> bool:
    return bool(PLACEHOLDER_RE.match(value))


def _key_segments(key: str) -> List[str]:
    # Split camelCase and PascalCase into words, then on separators.
    spaced = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", key)
    parts = re.split(r"[\s_\-.]+", spaced)
    return [p.lower() for p in parts if p]


def _key_is_secretish(key: str) -> bool:
    segments = _key_segments(key)
    if any(seg in SECRET_KEY_HINTS for seg in segments):
        return True
    normalized = re.sub(r"[\s_\-.]+", "", key).lower()
    return any(compound in normalized for compound in SECRET_KEY_COMPOUNDS)


def _looks_high_entropy(value: str) -> bool:
    if not HIGH_ENTROPY_RE.match(value):
        return False
    # Require at least two character classes to avoid flagging plain slugs.
    classes = 0
    if re.search(r"[a-z]", value):
        classes += 1
    if re.search(r"[A-Z]", value):
        classes += 1
    if re.search(r"[0-9]", value):
        classes += 1
    if re.search(r"[+/=_\-]", value):
        classes += 1
    return classes >= 2


def _preview(value: str) -> str:
    value = value.strip()
    if len(value) <= 8:
        return "***"
    return f"{value[:3]}***{value[-2:]} (len={len(value)})"


def _walk(node, trail: str) -> Iterator[Tuple[str, str, str]]:
    """Yield (json_path, key, value) for every string leaf."""
    if isinstance(node, dict):
        for key, val in node.items():
            child_trail = f"{trail}.{key}" if trail else key
            if isinstance(val, str):
                yield child_trail, str(key), val
            else:
                yield from _walk(val, child_trail)
    elif isinstance(node, list):
        for idx, val in enumerate(node):
            child_trail = f"{trail}[{idx}]"
            if isinstance(val, str):
                yield child_trail, "", val
            else:
                yield from _walk(val, child_trail)


def scan_value(json_path: str, key: str, value: str) -> List[Finding]:
    findings: List[Finding] = []
    # 1) Vendor token shapes anywhere, regardless of key.
    for name, pattern in TOKEN_PATTERNS:
        if pattern.search(value):
            findings.append(Finding(Path("<pending>"), json_path, f"matches {name} pattern", _preview(value)))
            return findings  # one strong signal is enough for this leaf
    # 2) Non-placeholder value under a credential-looking key.
    if _key_is_secretish(key) and value.strip() and not _is_placeholder(value):
        # URLs under auth-ish keys are usually endpoints, not secrets.
        if not value.strip().lower().startswith(("http://", "https://")):
            if _looks_high_entropy(value) or len(value.strip()) >= 12:
                findings.append(
                    Finding(Path("<pending>"), json_path, f"non-placeholder value under secret-like key '{key}'", _preview(value))
                )
    return findings


def scan_file(path: Path) -> List[Finding]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ScanError(f"{path}: could not parse JSON: {exc}") from exc
    findings: List[Finding] = []
    for json_path, key, value in _walk(data, ""):
        for finding in scan_value(json_path, key, value):
            finding.path = path
            findings.append(finding)
    return findings


class ScanError(Exception):
    pass


def iter_config_files(root: Path) -> Iterator[Path]:
    seen = set()
    for pattern in CONFIG_GLOBS:
        for match in sorted(root.glob(pattern)):
            if not match.is_file():
                continue
            if any(part in SKIP_DIRS for part in match.relative_to(root).parts[:-1]):
                continue
            resolved = match.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            yield match


def run(root: Path, files: Iterable[Path] | None = None) -> Tuple[List[Finding], List[str]]:
    findings: List[Finding] = []
    errors: List[str] = []
    targets = list(files) if files is not None else list(iter_config_files(root))
    for path in targets:
        try:
            findings.extend(scan_file(path))
        except ScanError as exc:
            errors.append(str(exc))
    return findings, errors


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Detect accidental secrets in plugin JSON configs.")
    parser.add_argument("--root", default=".", help="Repository root to scan (default: current dir).")
    parser.add_argument("files", nargs="*", help="Optional explicit JSON files to scan instead of auto-discovery.")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    if not root.exists():
        print(f"error: root does not exist: {root}", file=sys.stderr)
        return 2

    explicit = [Path(f) for f in args.files] if args.files else None
    findings, errors = run(root, explicit)

    for err in errors:
        print(f"error: {err}", file=sys.stderr)

    scanned = len(explicit) if explicit is not None else len(list(iter_config_files(root)))
    if findings:
        print(f"FAIL: {len(findings)} potential secret(s) found in plugin configs:\n", file=sys.stderr)
        for finding in findings:
            rel = finding.path
            try:
                rel = finding.path.relative_to(root)
            except ValueError:
                pass
            print(f"  - {rel}: {finding.json_path}: {finding.reason} [{finding.preview}]", file=sys.stderr)
        print("\nRemove the credential and use a runtime placeholder (empty string / OAuth / Bearer header).", file=sys.stderr)
        return 1

    if errors:
        return 2

    print(f"OK: scanned {scanned} plugin config(s); no secrets detected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
