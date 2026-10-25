---
name: framer
description: Use when the user wants to read, edit, audit or publish a Framer site or its CMS through Framer's official hosted MCP server (OAuth, no API key).
---

# Framer (official hosted MCP)

Server: `https://mcp.framer.com/mcp` (Streamable HTTP). Auth is browser OAuth handled by the client: the user signs in to Framer and approves the connection. The plugin holds no API key, token or env var. Never ask the user to paste a Framer API key into chat.

## Safe workflow
1. **Read first.** Open the project (ask for the full project link if unsure), list pages, read structure/CMS. Summarize before proposing changes.
2. **Branch/draft, not live.** Make changes in a branch or unpublished state when available. Show the user what will change.
3. **Never publish or deploy without an explicit OK** for that exact change in this conversation.
4. **friskydev.com stays DARK by default:** do not publish, republish, promote a branch or change domains for the friskydev.com project unless the owner explicitly says so for that change.
5. Large edits (many nodes, deletes) need a confirmation and a rollback note (last published version id).

## Auth errors
401 / "Missing Authorization header" means the client has not completed OAuth: tell the user to reconnect Framer in the client and approve in the browser. Do not fall back to an API key.

## Limits
Localization is not in the hosted MCP at launch (Framer points to the local `@framer/agent` CLI for that). Permissions equal the signed-in Framer account.
