#!/usr/bin/env python3
"""Generate a CycloneDX SBOM for the packaged plugins in this marketplace.

The marketplace "packages" plugins as folders containing a ``kimi.plugin.json``
manifest. Each manifest may declare one or more ``mcpServers`` entries that are
either:

* a hosted endpoint (``{"url": "https://..."}``), or
* a locally launched process (``{"command": "npx", "args": [...]}``) that pulls
  in an external package (often pinned, e.g. ``convex@1.45.0``).

This script walks the repo, reads every manifest listed in ``plugins.json``,
and emits a CycloneDX 1.5 JSON SBOM to ``sbom/plugins.cdx.json``. The SBOM lists
each plugin as a component, and attaches the MCP endpoints / npm packages it
depends on as sub-components so a reviewer can see exactly what each packaged
plugin wires in.

No secrets are read or emitted: ``env`` values in manifests are intentionally
ignored (they are placeholders), and only the *keys* are recorded as required
configuration. The script uses only the Python standard library so it runs in
CI without any installs.

Usage:
    python3 scripts/generate_sbom.py            # write sbom/plugins.cdx.json
    python3 scripts/generate_sbom.py --check    # verify committed SBOM is current
    python3 scripts/generate_sbom.py --stdout   # print SBOM, do not write
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INDEX_FILE = REPO_ROOT / "plugins.json"
OUTPUT_FILE = REPO_ROOT / "sbom" / "plugins.cdx.json"

# Fixed values keep the SBOM byte-for-byte deterministic so --check works in CI
# without a clock/UUID causing spurious diffs. Update SBOM_SERIAL when the SBOM
# format meaningfully changes.
SBOM_SPEC_VERSION = "1.5"
SBOM_SERIAL = "urn:uuid:00000000-0000-0000-0000-00000000f36b"
BOM_FORMAT = "CycloneDX"

# npm packages that can be referenced in purls without an explicit scope.
_NPM_SPEC = re.compile(r"^(?P<name>(?:@[^/]+/)?[^@/][^@]*?)(?:@(?P<version>.+))?$")


def _bom_ref(*parts: str) -> str:
    return "/".join(p for p in parts if p)


def _npm_purl(spec: str) -> tuple[str, str | None, str]:
    """Return (name, version, purl) for an npm package spec like ``convex@1.45.0``."""
    match = _NPM_SPEC.match(spec)
    if not match:
        return spec, None, f"pkg:npm/{spec}"
    name = match.group("name")
    version = match.group("version")
    purl = f"pkg:npm/{name}"
    if version:
        purl += f"@{version}"
    return name, version, purl


def _mcp_components(plugin_name: str, mcp_servers: dict) -> list[dict]:
    """Build sub-components for a plugin's declared MCP servers."""
    components: list[dict] = []
    for server_name in sorted(mcp_servers):
        server = mcp_servers[server_name] or {}
        if "url" in server and server["url"]:
            url = server["url"]
            components.append(
                {
                    "bom-ref": _bom_ref(plugin_name, "mcp", server_name, url),
                    "type": "service",
                    "name": server_name,
                    "description": f"Hosted MCP endpoint for {plugin_name}",
                    "externalReferences": [
                        {"type": "service", "url": url}
                    ],
                    "properties": [
                        {"name": "mcp:transport", "value": "hosted"},
                        {"name": "mcp:endpoint", "value": url},
                    ],
                }
            )
        elif server.get("command"):
            args = server.get("args") or []
            # Record which env var *keys* must be supplied (never the values).
            env_keys = sorted((server.get("env") or {}).keys())
            # The external dependency is the first non-flag arg after the runner
            # (e.g. npx -y convex@1.45.0 -> convex@1.45.0).
            pkg_spec = None
            if server.get("command") in {"npx", "pnpm", "yarn", "bunx"}:
                for arg in args:
                    if arg.startswith("-"):
                        continue
                    pkg_spec = arg
                    break
            comp: dict = {
                "bom-ref": _bom_ref(plugin_name, "mcp", server_name),
                "type": "application",
                "name": server_name,
                "description": f"Local MCP process for {plugin_name}",
                "properties": [
                    {"name": "mcp:transport", "value": "local"},
                    {
                        "name": "mcp:command",
                        "value": " ".join([server["command"], *args]),
                    },
                ],
            }
            if env_keys:
                comp["properties"].append(
                    {"name": "mcp:requiredEnv", "value": ",".join(env_keys)}
                )
            if pkg_spec:
                name, version, purl = _npm_purl(pkg_spec)
                comp["purl"] = purl
                comp["properties"].append(
                    {"name": "mcp:package", "value": pkg_spec}
                )
                if version:
                    comp["version"] = version
            components.append(comp)
    return components


def build_sbom() -> dict:
    index = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    plugins = index.get("plugins", [])

    components: list[dict] = []
    for entry in sorted(plugins, key=lambda p: p["name"]):
        name = entry["name"]
        rel_path = entry.get("path", f"./{name}")
        manifest_path = (REPO_ROOT / rel_path / "kimi.plugin.json").resolve()

        component: dict = {
            "bom-ref": _bom_ref("plugin", name),
            "type": "application",
            "name": name,
            "description": entry.get("description", ""),
            "properties": [
                {"name": "marketplace:path", "value": rel_path},
                {"name": "marketplace:category", "value": entry.get("category", "")},
                {"name": "marketplace:owner", "value": entry.get("owner", "")},
            ],
        }

        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest.get("version"):
                component["version"] = manifest["version"]
            if manifest.get("license"):
                component["licenses"] = [
                    {"license": {"id": manifest["license"]}}
                ]
            if manifest.get("author"):
                component["author"] = manifest["author"]
            sub = _mcp_components(name, manifest.get("mcpServers") or {})
            if sub:
                component["components"] = sub
            component["properties"].append(
                {"name": "marketplace:manifest", "value": "kimi.plugin.json"}
            )
        else:
            component["properties"].append(
                {"name": "marketplace:manifest", "value": "missing"}
            )

        # Drop empty-string properties to keep the SBOM tidy.
        component["properties"] = [
            p for p in component["properties"] if p["value"] != ""
        ]
        components.append(component)

    sbom = {
        "bomFormat": BOM_FORMAT,
        "specVersion": SBOM_SPEC_VERSION,
        "serialNumber": SBOM_SERIAL,
        "version": 1,
        "metadata": {
            "component": {
                "bom-ref": "marketplace",
                "type": "application",
                "name": index.get("name", "frisky"),
                "description": "Frisky Marketplace — packaged Kimi plugins",
            },
            "properties": [
                {"name": "marketplace:pluginCount", "value": str(len(components))},
            ],
        },
        "components": components,
    }
    return sbom


def _serialize(sbom: dict) -> str:
    return json.dumps(sbom, indent=2, ensure_ascii=False, sort_keys=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--check",
        action="store_true",
        help="exit non-zero if the committed SBOM differs from a fresh build",
    )
    group.add_argument(
        "--stdout",
        action="store_true",
        help="print the SBOM to stdout instead of writing the file",
    )
    args = parser.parse_args(argv)

    sbom = build_sbom()
    rendered = _serialize(sbom)

    if args.stdout:
        sys.stdout.write(rendered)
        return 0

    if args.check:
        if not OUTPUT_FILE.exists():
            print(f"SBOM missing: {OUTPUT_FILE} (run generate_sbom.py)", file=sys.stderr)
            return 1
        current = OUTPUT_FILE.read_text(encoding="utf-8")
        if current != rendered:
            print(
                "SBOM is out of date. Run: python3 scripts/generate_sbom.py",
                file=sys.stderr,
            )
            return 1
        print("SBOM is up to date.")
        return 0

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(rendered, encoding="utf-8")
    print(f"Wrote {OUTPUT_FILE.relative_to(REPO_ROOT)} ({len(sbom['components'])} plugins)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
