# Frisky Dev MCP client setup

## Claude Code

Add this repository as a marketplace, then install `frisky-dev-mcp@frisky-dev`,
`frisky-dev-make@frisky-dev`, or `frisky-dev-n8n@frisky-dev`.
`.claude-plugin/marketplace.json` is the Claude catalog; `.agents` is retained for compatibility.
Frisky uses browser OAuth discovery, not a required static `FRISKY_MCP_TOKEN` header.
Make requires `MAKE_MCP_URL` and `MAKE_MCP_TOKEN`; n8n Cloud requires `N8N_MCP_TOKEN`.
Load credentials from the vault into the client environment; never commit them.

## Grok

`.grok-plugin/marketplace.json` is the personal catalog. All three plugin folders
have `.grok-plugin/plugin.json` and `.mcp.json`.
This does not submit or publish anything to xAI's official catalog.
For an official submission, use `scripts/build-grok-submissions.py --sha <40-character-commit>`
after the source commit is pushed; review the generated entries in the output directory.
The generator pins the source commit and plugin subdirectory. A private source repository
may not be fetchable by xAI; do not make a repository public without approval.
Actual installation in Grok remains an acceptance test, not a claim made by JSON validation.

## Mistral Vibe

Requires Python 3.11+ to render/validate the template:

```sh
python3 scripts/render-vibe-config.py --output /tmp/frisky-vibe.toml
```

The renderer reads `MAKE_MCP_URL`, creates a new mode-600 file, and never overwrites
`~/.vibe/config.toml`. Review locally and append only missing entries.
A Make toolbox URL may itself be sensitive; keep the generated file private.
Token values stay outside config: `[mcp_servers.auth].api_key_env` holds their variable names.
Frisky uses OAuth with scope `frisky.mcp`; Vibe stores OAuth tokens in the OS keyring.
For headless clients use an approved machine identity instead; do not copy human tokens.
After configuring, run `/mcp login frisky-dev-mcp` and `/mcp status` in Vibe.

## Le Chat

`mistral/connectors.json` is a human setup worksheet, not a documented import schema.
Create connectors in Le Chat manually using its private secret fields and real URLs.
Use OAuth for Frisky when supported; bearer tokens for Make and n8n Cloud.

## Two distinct n8n installations

- New `frisky-dev-n8n`: `https://frisky.app.n8n.cloud/mcp-server/http`.
- Existing Kimi `n8n-connector`: `https://n8n.friskydev.com/mcp-server/http` (self-hosted).

They are not the same endpoint. The legacy Kimi entry is preserved, not silently migrated.

## Validation and limits

Run `python3 scripts/validate-marketplace.py` and
`python3 -m unittest discover -s tests -v`.
These check structure, local paths, cross-client manifests, and secret-free rendering;
they do not prove authenticated tool execution or host-client compatibility.
No deploy, DNS, Access policy, merge, credential rotation, or Kimi change is performed here.

## Reference documentation

- https://docs.mistral.ai/vibe/code/cli/mcp-servers
- https://code.claude.com/docs/en/plugins/manifest-reference
- https://github.com/xai-org/plugin-marketplace/blob/main/.grok-plugin/marketplace.json
