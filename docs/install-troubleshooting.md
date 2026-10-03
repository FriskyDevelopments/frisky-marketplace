# Install troubleshooting

Use this guide when adding the marketplace or connecting an installed plugin in
the Kimi app. Start with the [Install steps](../README.md#install). Installing a
plugin and authorizing its MCP connection are separate steps; a visible plugin
does not prove that its tools can connect.

## Catalog missing or out of date

- Add `https://github.com/FriskyDevelopments/frisky-marketplace` in **Directory →
  Organization**, not a plugin folder URL or the GitHub page for `plugins.json`.
- Confirm that the repository is accessible to the account used for installation.
- The app re-fetches the catalog periodically. Reopen the Directory and allow for
  its next fetch; this repository does not specify a refresh interval.
- If only one plugin is missing, check its entry in [`plugins.json`](../plugins.json)
  and that its `path` contains `kimi.plugin.json`. Report an index or manifest
  problem rather than changing the catalog just to force a refresh.

## Plugin installed, but tools fail

| Symptom | What to check next |
| --- | --- |
| Sign-in never finishes | Complete the provider's authorization flow using the intended account, then retry a read-only tool. If the callback is blocked, check browser popup and network restrictions. |
| `401` / unauthorized | Reconnect using the provider's supported sign-in or credential setup. A credential may be missing, expired, or revoked. Do not paste it into chat or an issue. |
| `403` / forbidden | Confirm the signed-in account has access to the requested organization, workspace, or project. Re-authentication alone may not fix permissions. Do not broaden permissions blindly. |
| Timeout, DNS, TLS, or connection error | Check connectivity from the environment running the MCP connection and the provider's service status. Use the endpoint in the plugin's `kimi.plugin.json`; do not disable TLS verification. |
| `npx` / command not found, or local server exits | Follow the local MCP checks below. Hosted connectors with a `url` do not require a local Node.js server. |
| Tools connect, but results are empty | Confirm the selected account and workspace/project. For n8n, the workflow must be marked **Available in MCP**; for Render, select the active workspace first. |

### Connector-specific setup

- **Cloudflare and n8n:** finish the provider OAuth flow and select/authorize the
  intended account. **Composio:** its own authorization does not replace the
  individual app connections in **Connect Apps**.
- **Render:** configure `Authorization: Bearer <RENDER_API_KEY>` in the private MCP
  connection configuration. The placeholder is not a real key. Render keys are
  broadly scoped; see the [Render instructions](../render/skills/render/SKILL.md).
- **Framer:** the shipped manifest has empty `FRAMER_PROJECT_URL` and
  `FRAMER_API_KEY` values. Supply both through private, local connection environment
  configuration, ensuring they reach the server process. Do not fill them into
  this repository. See the [Framer instructions](../framer/skills/framer/SKILL.md)
  for the expected project URL and key source.
- **Convex:** authenticate in the environment running the server with
  `npx convex@1.45.0 login`, then use the correct Convex project directory for tool
  calls. The manifest pins `convex@1.45.0`; see the
  [Convex instructions](../convex-connector/skills/convex-connector/SKILL.md).
- **Folios:** its manifest has no `mcpServers` entry. It provides
  [skill instructions](../folios/skills/folios/SKILL.md), not an MCP connection;
  absence of MCP tools is not itself an installation failure.

## Local MCP checks (Convex and Framer)

Run these non-secret checks in the environment where Kimi launches the MCP server,
not merely in a separate terminal or cloud checkout:

```sh
node --version
npx --version
```

Both commands should return a version instead of “command not found.” Ensure that
environment has Node.js and npm/npx on its `PATH`, then restart the app after
changing its environment. The first `npx` launch needs access to the npm registry
to download the package. Check network/proxy restrictions if that download fails.
Do not replace manifest commands or upgrade packages as a first troubleshooting
step. A successful version check proves prerequisites only, not authentication.

## Verify recovery and report a remaining problem

Retry installation or authorization, then request one read-only operation, such
as listing workspaces or reading project status, on an account you are authorized
to access. Success means the plugin appears and its expected read-only operation
works; Folios should instead expose its skill instructions. Do not test by
publishing, deploying, modifying data, or changing environment variables.

If it still fails, report the plugin name and version from `kimi.plugin.json`,
Kimi app version, OS/runtime, failure stage (catalog, install, authorization, or
tool call), timestamp/timezone, and a redacted error message. State what you tried.
Never include credentials, authorization headers, callback URLs with codes,
private project data, or unredacted logs/screenshots. If a secret was exposed,
revoke or rotate it with the provider before sharing further evidence.
