#!/usr/bin/env python3
"""Tests for scripts/scan_secrets.py (stdlib unittest, no dependencies).

All "secret-looking" values below are synthetic, non-functional strings built
only to exercise the detector's regexes. None are real credentials.

Run: python3 scripts/test_scan_secrets.py
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import scan_secrets  # noqa: E402


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")


class CleanRepoTests(unittest.TestCase):
    def test_real_repo_is_clean(self):
        # The actual marketplace repo must pass with no findings.
        repo_root = Path(__file__).resolve().parent.parent
        findings, errors = scan_secrets.run(repo_root)
        self.assertEqual(errors, [], f"unexpected parse errors: {errors}")
        self.assertEqual(
            findings,
            [],
            "real repo should contain no secrets, got:\n"
            + "\n".join(str(f) for f in findings),
        )

    def test_placeholders_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(
                root / "demo" / "kimi.plugin.json",
                {
                    "name": "demo",
                    "mcpServers": {
                        "demo": {
                            "command": "npx",
                            "args": ["-y", "demo-mcp-server"],
                            "env": {
                                "DEMO_PROJECT_URL": "",
                                "DEMO_API_KEY": "",
                                "DEMO_TOKEN": "<token>",
                                "DEMO_SECRET": "YOUR_API_KEY",
                            },
                            "url": "https://api.example.com/mcp",
                        }
                    },
                },
            )
            findings, errors = scan_secrets.run(root)
            self.assertEqual(errors, [])
            self.assertEqual(findings, [], [str(f) for f in findings])

    def test_endpoint_urls_not_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(
                root / "plugins.json",
                {"name": "x", "authUrl": "https://auth.example.com/oauth"},
            )
            findings, _ = scan_secrets.run(root)
            self.assertEqual(findings, [], [str(f) for f in findings])


class PlantedSecretTests(unittest.TestCase):
    """Each case plants one synthetic, non-functional token shape."""

    def _scan_single(self, obj) -> list:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(root / "leak" / "kimi.plugin.json", obj)
            findings, errors = scan_secrets.run(root)
            self.assertEqual(errors, [])
            return findings

    def test_aws_access_key_shape(self):
        findings = self._scan_single({"env": {"NOTE": "AKIA" + "A" * 16}})
        self.assertTrue(findings)

    def test_github_token_shape(self):
        findings = self._scan_single({"ghToken": "ghp_" + "A" * 36})
        self.assertTrue(findings)

    def test_openai_key_shape(self):
        findings = self._scan_single({"desc": "sk-" + "A" * 32})
        self.assertTrue(findings)

    def test_private_key_block(self):
        findings = self._scan_single(
            {"env": {"KEY": "-----BEGIN RSA PRIVATE KEY-----\nAAAA\n-----END RSA PRIVATE KEY-----"}}
        )
        self.assertTrue(findings)

    def test_secret_key_with_opaque_value(self):
        # Under a secret-like key, a long opaque mixed value is flagged.
        findings = self._scan_single({"env": {"API_KEY": "Ab12Cd34Ef56Gh78Ij90Kl"}})
        self.assertTrue(findings)

    def test_bearer_inline(self):
        findings = self._scan_single({"headers": {"Authorization": "Bearer " + "x" * 24}})
        self.assertTrue(findings)

    def test_exit_code_on_planted_secret(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(root / "leak" / "kimi.plugin.json", {"token": "ghp_" + "B" * 36})
            rc = scan_secrets.main(["--root", str(root)])
            self.assertEqual(rc, 1)

    def test_exit_code_on_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(root / "ok" / "kimi.plugin.json", {"env": {"API_KEY": ""}})
            rc = scan_secrets.main(["--root", str(root)])
            self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
