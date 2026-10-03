# Plugin Permissions & Data Access

This document inventories every plugin published in this marketplace and
describes, for each one, **how it connects**, **how it authenticates**, **what
network egress it causes**, and **what data it can read or write**.

It is generated from — and must stay consistent with — each plugin's
`kimi.plugin.json` manifest (`mcpServers` block) and `plugins.json`. Run
`python3 scripts/check_permissions.py` to verify the two stay in sync and that
no secrets are committed to any manifest.

> **No secrets live in this repo.** Every manifest ships with empty or absent
> credential fields. Auth is completed interactively by the user at install /
> first use (OAuth) or by pasting an API key / token into the app at runtime —
> never into a file in this repo. Placeholders below use `<...>` notation.

## Connection types

| Type | Meaning | Trust / egress notes |
|------|---------|----------------------|
| **Hosted MCP (remote URL)** | The app connects to a vendor-run MCP server over HTTPS (`url` in the manifest). | Session data and tool arguments leave your machine and transit to the vendor endpoint. |
| **Local MCP (spawned command)** | The app spawns a process locally (`command` + `args`, typically `npx`). | The command runs on your machine; it may itself make outbound calls to the vendor's API. |

## Auth models

| Model | Meaning |
|-------|---------|
| **OAuth** | Interactive browser sign-in on first use; no credential stored in-repo. |
| **API key / token** | User supplies a key at runtime (app connect dialog or env var); placeholder only in-repo. |
| **Local project context** | Local CLI uses whatever Convex/project credentials already exist in the user's environment; nothing in-repo. |
| **None (static)** | Plugin ships no MCP server; it is skill/content only, no auth, no egress. |

---

## Per-plugin inventory

### 01 · sentry-connector
- **Category:** `DEVELOPER_TOOLS`
- **Connection:** Hosted MCP — `https://mcp.sentry.dev/mcp`
- **Auth:** OAuth (Sentry sign-in on first use)
- **Network egress:** HTTPS to `mcp.sentry.dev`
- **Data access:** Read monitoring data — errors, issues, events, releases, traces, session replays. Read-oriented observability data.

### 02 · composio-connector
- **Category:** `PRODUCTIVITY`
- **Connection:** Hosted MCP — `https://connect.composio.dev/mcp`
- **Auth:** OAuth via Composio; per-app account authorization done at `connect.composio.dev` (Connect Apps)
- **Network egress:** HTTPS to `connect.composio.dev`, which in turn brokers calls to 1000+ downstream apps (Gmail, Slack, Notion, Linear, HubSpot, ...)
- **Data access:** Broad. Acts as a tool router — can read and write across whichever third-party apps the user connects. Scope is as wide as the apps the user authorizes in Composio.

### 03 · convex-connector
- **Category:** `DEVELOPER_TOOLS`
- **Connection:** Local MCP — `npx -y convex@1.45.0 mcp start`
- **Auth:** Local project context (uses the user's existing Convex CLI/project credentials; nothing stored in-repo)
- **Network egress:** The local `convex` CLI talks to the user's Convex deployment(s)
- **Data access:** Deployment status, browse tables, query data, run functions, read logs & performance insights, manage environment variables. Can read application data and modify env vars on the user's Convex project.

### 04 · friskydev-mcp
- **Category:** `PRODUCTIVITY`
- **Connection:** Hosted MCP — `https://mcp.friskydev.com/mcp`
- **Auth:** Handled by the FriskyDev gateway at the endpoint (no credential in-repo)
- **Network egress:** HTTPS to `mcp.friskydev.com`
- **Data access:** 15 specialist operators backed by a shared MongoDB memory. Can read and write that shared memory spine. Session content transits to the FriskyDev gateway.

### 05 · render
- **Category:** `DEVTOOLS`
- **Connection:** Hosted MCP — `https://mcp.render.com/mcp`
- **Auth:** API key / token — user creates a Render API key (Dashboard → Account Settings → API Keys) and connects with `Authorization: Bearer <key>`; placeholder only in-repo
- **Network egress:** HTTPS to `mcp.render.com`
- **Data access:** List workspaces/services; create web services, static sites, cron jobs, Postgres DBs, Key-Value stores; inspect deploys; read logs & metrics; update env vars; run **read-only** SQL on Render Postgres. Create/update supported; the server does **not** delete services, trigger manual deploys, or change scaling.

### 06 · framer
- **Category:** `PRODUCTIVITY`
- **Connection:** Local MCP — `npx -y framer-mcp-server`
- **Auth:** API key / token via env vars — `FRAMER_PROJECT_URL` and `FRAMER_API_KEY` (both ship **empty** in the manifest; user fills them at runtime)
- **Network egress:** The local `framer-mcp-server` process talks to Framer's API for the configured project
- **Data access:** Read pages and project context, manage CMS collections, apply changes, preview, and publish/deploy the Framer site. Read and write (including publish) on the configured Framer project.

### 07 · chatprd
- **Category:** `PRODUCTIVITY`
- **Connection:** Hosted MCP — `https://app.chatprd.ai/mcp`
- **Auth:** OAuth (no API key)
- **Network egress:** HTTPS to `app.chatprd.ai`
- **Data access:** Push PRDs, feature specs, and the FriskyClaw ops rollup into ChatPRD; read back PRD status. Read and write product docs.

### 08 · folios
- **Category:** `PRODUCTIVITY`
- **Connection:** None — no `mcpServers` declared; skill/content only (`./skills/`)
- **Auth:** None (static)
- **Network egress:** None from the plugin itself
- **Data access:** None at the MCP layer. Ships skill instructions only (bilingual evidence-workspace Playbooks). No tools, no egress, no credentials.

### 09 · cloudflare-connector
- **Category:** `DEVELOPER_TOOLS`
- **Connection:** Hosted MCP — `https://mcp.cloudflare.com/mcp`
- **Auth:** OAuth (Cloudflare sign-in; user selects allowed accounts)
- **Network egress:** HTTPS to `mcp.cloudflare.com`
- **Data access:** Manage the full Cloudflare resource set — Workers, Pages, KV, D1, R2, DNS, Zero Trust, Analytics, Stream, tunnels. Broad read/write over the authorized Cloudflare account(s).

### 10 · n8n-connector
- **Category:** `PRODUCTIVITY`
- **Connection:** Hosted MCP (self-hosted) — `https://n8n.friskydev.com/mcp-server/http`
- **Auth:** OAuth at the n8n instance level (sign in to `n8n.friskydev.com` and approve). Only workflows marked **Available in MCP** are executable.
- **Network egress:** HTTPS to the user's self-hosted `n8n.friskydev.com`
- **Data access:** Search and trigger workflows, create/edit workflows and data tables, manage execution records. Read and write on the self-hosted n8n instance.

### 11 · perplexity
- **Category:** `PRODUCTIVITY`
- **Connection:** Hosted MCP — `https://api.perplexity.ai/mcp`
- **Auth:** OAuth (pick API org to bill) **or** API key; placeholder only in-repo
- **Network egress:** HTTPS to `api.perplexity.ai`
- **Data access:** Real-time web search and reasoning tools. Sends queries out to Perplexity; returns search/reasoning results. No access to local resources.

### 12 · magic-patterns
- **Category:** `PRODUCTIVITY`
- **Connection:** Hosted MCP — `https://mcp.magicpatterns.com/mcp`
- **Auth:** OAuth **or** Magic Patterns API key; placeholder only in-repo
- **Network egress:** HTTPS to `mcp.magicpatterns.com`
- **Data access:** Prototype UI seeded from local UI, generate design directions, port local UI into hosted designs, adapt designs back to production code. Local UI snippets you share transit to Magic Patterns' hosted service.

---

## Summary matrix

| # | Plugin | Connection | Auth | Primary egress host | Data access breadth |
|---|--------|-----------|------|---------------------|---------------------|
| 01 | sentry-connector | Hosted MCP | OAuth | mcp.sentry.dev | Read observability data |
| 02 | composio-connector | Hosted MCP | OAuth (per-app) | connect.composio.dev | Broad — 1000+ connected apps (R/W) |
| 03 | convex-connector | Local (npx) | Local project context | user's Convex deployment | R data + manage env vars |
| 04 | friskydev-mcp | Hosted MCP | Gateway | mcp.friskydev.com | R/W shared MongoDB memory |
| 05 | render | Hosted MCP | API key (Bearer) | mcp.render.com | Create/update infra, read-only SQL |
| 06 | framer | Local (npx) | API key (env vars) | Framer API | R/W + publish site |
| 07 | chatprd | Hosted MCP | OAuth | app.chatprd.ai | R/W product docs |
| 08 | folios | None (skill only) | None | — | None |
| 09 | cloudflare-connector | Hosted MCP | OAuth | mcp.cloudflare.com | Broad — full Cloudflare account (R/W) |
| 10 | n8n-connector | Hosted MCP (self-hosted) | OAuth (instance) | n8n.friskydev.com | R/W workflows & data tables |
| 11 | perplexity | Hosted MCP | OAuth or API key | api.perplexity.ai | Web search / reasoning |
| 12 | magic-patterns | Hosted MCP | OAuth or API key | mcp.magicpatterns.com | R/W design prototypes |

## Reviewer notes

- **Highest-breadth plugins:** `composio-connector` and `cloudflare-connector`
  grant the widest access (many downstream apps / a full Cloudflare account).
  Treat their OAuth consent screens as the real scope-granting step.
- **Credential handling:** `render`, `framer`, `perplexity`, and
  `magic-patterns` take an API key at runtime. The `framer` manifest declares
  the env keys `FRAMER_PROJECT_URL` / `FRAMER_API_KEY` with **empty** values —
  confirm they remain empty in-repo.
- **Local execution:** `convex-connector` and `framer` spawn processes via
  `npx`; these run on the user's machine with the user's environment.
- **No-egress plugin:** `folios` declares no MCP server and causes no network
  access on its own.
