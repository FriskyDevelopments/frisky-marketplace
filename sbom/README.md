# SBOM — Software Bill of Materials

This marketplace publishes a machine-readable SBOM for every **packaged
plugin** so consumers can audit what each plugin wires into their chats before
installing.

- **Artifact:** [`plugins.cdx.json`](./plugins.cdx.json)
- **Format:** [CycloneDX](https://cyclonedx.org/) 1.5 (JSON)
- **Generator:** [`scripts/generate_sbom.py`](../scripts/generate_sbom.py) (Python 3 stdlib only)

## What's in it

The SBOM is derived from `plugins.json` and each plugin's `kimi.plugin.json`
manifest. For every plugin it records:

| Field | Source |
|-------|--------|
| name / version / license / author | `kimi.plugin.json` |
| path / category / owner | `plugins.json` |
| MCP endpoints and local processes | `kimi.plugin.json` → `mcpServers` |

Each declared MCP server becomes a sub-component:

- **Hosted** servers (`{"url": "..."}`) → CycloneDX `service` with the endpoint
  recorded under `externalReferences`.
- **Local** servers (`{"command": "npx", "args": [...]}`) → CycloneDX
  `application` with a [`purl`](https://github.com/package-url/purl-spec)
  (e.g. `pkg:npm/convex@1.45.0`) for the pinned package, plus the resolved
  command line.

### Secrets

The generator **never** emits secret values. Where a manifest declares an `env`
block (e.g. `FRAMER_API_KEY`), only the **key names** are recorded as required
configuration under the `mcp:requiredEnv` property. Values are ignored.

## Regenerate

```bash
python3 scripts/generate_sbom.py            # rewrite sbom/plugins.cdx.json
python3 scripts/generate_sbom.py --stdout   # preview without writing
python3 scripts/generate_sbom.py --check    # CI: fail if the file is stale
```

Output is deterministic (fixed serial number, stable ordering), so a clean
regenerate produces no diff unless a manifest actually changed. Commit the
updated `sbom/plugins.cdx.json` whenever you add or change a plugin.

## Validate

```bash
python3 tests/test_sbom.py
```

The test cross-checks the SBOM against every manifest, confirms no secret
values leak, and asserts the committed file matches a fresh build.

## CI

[`.github/workflows/sbom.yml`](../.github/workflows/sbom.yml) runs the
`--check` and the test on every push/PR, uploads the SBOM as a build artifact,
and attaches it to published GitHub Releases.
