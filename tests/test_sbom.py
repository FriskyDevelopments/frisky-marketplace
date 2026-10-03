#!/usr/bin/env python3
"""Tests for the plugin SBOM generator.

Runs with plain ``python3 tests/test_sbom.py`` — no pytest or third-party deps
required. Exits 0 on success, 1 on failure, and prints a short report.

What it checks:
1. The generator produces a valid CycloneDX envelope.
2. Every plugin in plugins.json appears exactly once as a component.
3. Each component's version/license mirror its kimi.plugin.json manifest.
4. Hosted MCP endpoints and pinned npm packages are captured as sub-components.
5. No secret values leak into the SBOM (only env var *keys* are allowed).
6. The committed sbom/plugins.cdx.json matches a fresh build (--check parity).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import generate_sbom  # noqa: E402

FAILURES: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        FAILURES.append(msg)


def load_index() -> dict:
    return json.loads((REPO_ROOT / "plugins.json").read_text(encoding="utf-8"))


def main() -> int:
    index = load_index()
    sbom = generate_sbom.build_sbom()

    # 1. Envelope.
    check(sbom.get("bomFormat") == "CycloneDX", "bomFormat should be CycloneDX")
    check(sbom.get("specVersion") == "1.5", "specVersion should be 1.5")
    check("components" in sbom, "SBOM must have components")

    # 2. One component per indexed plugin.
    index_names = sorted(p["name"] for p in index["plugins"])
    comp_names = sorted(c["name"] for c in sbom["components"])
    check(
        index_names == comp_names,
        f"component set mismatch: index={index_names} sbom={comp_names}",
    )

    comp_by_name = {c["name"]: c for c in sbom["components"]}

    # 3 & 4. Per-plugin manifest mirroring + MCP sub-components.
    for entry in index["plugins"]:
        name = entry["name"]
        comp = comp_by_name.get(name)
        if comp is None:
            FAILURES.append(f"{name}: missing component")
            continue
        manifest_path = REPO_ROOT / entry.get("path", f"./{name}") / "kimi.plugin.json"
        if not manifest_path.exists():
            continue
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        if manifest.get("version"):
            check(
                comp.get("version") == manifest["version"],
                f"{name}: version mismatch ({comp.get('version')} != {manifest['version']})",
            )
        if manifest.get("license"):
            lic = (comp.get("licenses") or [{}])[0].get("license", {}).get("id")
            check(lic == manifest["license"], f"{name}: license mismatch ({lic})")

        servers = manifest.get("mcpServers") or {}
        sub = comp.get("components", [])
        check(
            len(sub) == len(servers),
            f"{name}: expected {len(servers)} mcp sub-components, got {len(sub)}",
        )
        for sname, server in servers.items():
            matches = [c for c in sub if c["name"] == sname]
            check(bool(matches), f"{name}: missing sub-component for mcp server {sname}")
            if not matches:
                continue
            scomp = matches[0]
            if server.get("url"):
                refs = scomp.get("externalReferences", [])
                check(
                    any(r.get("url") == server["url"] for r in refs),
                    f"{name}/{sname}: endpoint url not recorded",
                )
            elif server.get("command"):
                props = {p["name"]: p["value"] for p in scomp.get("properties", [])}
                check(
                    props.get("mcp:transport") == "local",
                    f"{name}/{sname}: expected local transport",
                )
                # Pinned npm package -> purl present.
                for arg in server.get("args") or []:
                    if "@" in arg and not arg.startswith("-"):
                        check(
                            scomp.get("purl", "").startswith("pkg:npm/"),
                            f"{name}/{sname}: pinned package missing purl",
                        )
                        break

    # 5. No secret values leak. Only env *keys* may appear; values must not.
    rendered = generate_sbom._serialize(sbom)
    for entry in index["plugins"]:
        manifest_path = REPO_ROOT / entry.get("path", f"./{entry['name']}") / "kimi.plugin.json"
        if not manifest_path.exists():
            continue
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for server in (manifest.get("mcpServers") or {}).values():
            for key, val in (server.get("env") or {}).items():
                check(key in rendered, f"env key {key} should be documented in SBOM")
                if val:  # non-empty secret value must never appear
                    check(val not in rendered, f"secret value for {key} leaked into SBOM")

    # 6. Committed artifact is up to date (deterministic --check parity).
    committed = REPO_ROOT / "sbom" / "plugins.cdx.json"
    check(committed.exists(), "sbom/plugins.cdx.json is missing")
    if committed.exists():
        check(
            committed.read_text(encoding="utf-8") == rendered,
            "committed sbom/plugins.cdx.json is stale — run scripts/generate_sbom.py",
        )

    if FAILURES:
        print("FAIL — {} problem(s):".format(len(FAILURES)))
        for f in FAILURES:
            print("  -", f)
        return 1
    print("OK — SBOM validated against {} plugins.".format(len(index["plugins"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
