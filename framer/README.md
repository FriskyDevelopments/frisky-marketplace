# framer — Framer hosted MCP, no API key

Connects Kimi to Framer's own hosted MCP server: `https://mcp.framer.com/mcp` (Streamable HTTP).

**No-key strategy.** Authentication is browser OAuth run by the client. You sign in to Framer and approve; the client keeps the session. This plugin contains no API keys, tokens or secret env vars, and there is nothing to paste.

**Privacy.** The plugin is only a manifest + skill. It stores no credentials and keeps no data; requests go directly from your client to Framer. Revoke access any time from your Framer account settings.

**Safety.** The skill reads first and asks before any write or publish; friskydev.com stays dark by default.

Framer is a trademark of its owner; this is an unofficial community plugin and the icon is original.
