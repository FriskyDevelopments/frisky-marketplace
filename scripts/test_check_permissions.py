#!/usr/bin/env python3
"""Tests for scripts/check_permissions.py.

Run with:
    python3 -m pytest scripts/test_check_permissions.py
or, with no pytest installed:
    python3 scripts/test_check_permissions.py

The tests use a temporary fake repo so they never depend on network access
and never execute any plugin.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_permissions as cp  # noqa: E402


def _write(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def _make_repo(tmp: Path, *, with_secret=False, documented=True) -> Path:
    index = {
        "name": "frisky",
        "plugins": [
            {"name": "alpha", "path": "./alpha"},
            {"name": "beta", "path": "./beta"},
        ],
    }
    _write(tmp / "plugins.json", index)
    _write(
        tmp / "alpha" / "kimi.plugin.json",
        {"name": "alpha", "mcpServers": {"alpha": {"url": "https://a.example/mcp"}}},
    )
    beta_manifest = {
        "name": "beta",
        "mcpServers": {
            "beta": {
                "command": "npx",
                "args": ["-y", "beta-mcp"],
                "env": {"BETA_API_KEY": "sk-REAL-SECRET" if with_secret else ""},
            }
        },
    }
    _write(tmp / "beta" / "kimi.plugin.json", beta_manifest)

    sections = "### alpha\n### beta\n" if documented else "### alpha\n"
    (tmp / "PERMISSIONS.md").write_text(sections, encoding="utf-8")
    return tmp


def test_find_secret_values_detects_populated_key():
    data = {"env": {"API_KEY": "sk-live-123"}}
    assert cp.find_secret_values(data) == ["env.API_KEY"]


def test_find_secret_values_ignores_empty_placeholder():
    data = {"env": {"API_KEY": "", "FRAMER_PROJECT_URL": ""}}
    assert cp.find_secret_values(data) == []


def test_find_secret_values_ignores_angle_placeholder():
    data = {"env": {"token": "<token>"}}
    assert cp.find_secret_values(data) == []


def test_clean_repo_passes(tmp_path):
    repo = _make_repo(tmp_path, with_secret=False, documented=True)
    assert cp.main(["check_permissions.py", str(repo)]) == 0


def test_undocumented_plugin_fails(tmp_path):
    repo = _make_repo(tmp_path, with_secret=False, documented=False)
    assert cp.main(["check_permissions.py", str(repo)]) == 1


def test_committed_secret_fails(tmp_path):
    repo = _make_repo(tmp_path, with_secret=True, documented=True)
    assert cp.main(["check_permissions.py", str(repo)]) == 1


def test_real_repo_passes():
    """The actual repo must pass its own checker."""
    repo_root = Path(__file__).resolve().parent.parent
    assert cp.main(["check_permissions.py", str(repo_root)]) == 0


def _run_without_pytest() -> int:
    import tempfile

    tests = [
        test_find_secret_values_detects_populated_key,
        test_find_secret_values_ignores_empty_placeholder,
        test_find_secret_values_ignores_angle_placeholder,
        test_real_repo_passes,
    ]
    tmp_tests = [
        test_clean_repo_passes,
        test_undocumented_plugin_fails,
        test_committed_secret_fails,
    ]
    failures = 0
    for t in tests:
        try:
            t()
            print(f"PASS {t.__name__}")
        except AssertionError as exc:
            failures += 1
            print(f"FAIL {t.__name__}: {exc}")
    for t in tmp_tests:
        with tempfile.TemporaryDirectory() as d:
            try:
                t(Path(d))
                print(f"PASS {t.__name__}")
            except AssertionError as exc:
                failures += 1
                print(f"FAIL {t.__name__}: {exc}")
    print()
    print("ALL PASSED" if failures == 0 else f"{failures} FAILED")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(_run_without_pytest())
