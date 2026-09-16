---
name: render
description: Use when the user asks about their Render.com cloud infrastructure — listing workspaces/services, checking deploy status, reading logs or metrics, creating web services, static sites, cron jobs, Postgres databases or Key Value stores, updating env vars, or querying Render Postgres with read-only SQL. Triggers on "Render", "my render services", "deploy on render", "render logs", "render postgres".
---

# Render (render.com)

Manage the user's Render cloud infrastructure through Render's **official hosted MCP server**
(`https://mcp.render.com/mcp`). All operations go through the `render` MCP tools — do not
scrape the Render dashboard and do not call the REST API directly unless the MCP server
lacks the needed capability.

## Authentication (first use)

The MCP connection needs a Render API key as a Bearer token. If MCP calls fail with
401/403 or "unauthorized":

1. Tell the user to create a key: Render Dashboard → **Account Settings → API Keys → Create API Key**.
   Warn them the key is broadly scoped across all their workspaces.
2. The user connects the hosted MCP server with `Authorization: Bearer <key>` (plugin/MCP
   connection UI). Never ask the user to paste the key into chat — it goes into the MCP
   connection configuration only.

## Standard flow

1. **Select the workspace first.** If the active workspace is unknown or calls come back
   empty/ambiguous, list workspaces and set the active one (e.g. "set my Render workspace
   to <name>"). Remember it for the rest of the conversation.
2. Then perform the requested operation (below).

## What the MCP server can do

- **Inventory**: list workspaces; list services with type/status; get one service's
  details (config + status).
- **Create**: web services, static sites, cron jobs, Render Postgres databases, Key Value
  instances. Collect repo URL, region, plan/instance type, build/start commands, and env
  vars from the user before creating; confirm the full spec with them first — creating a
  service can incur billing.
- **Deploys**: list deploy history for a service, get a specific deploy's details.
- **Logs & metrics**: filter service logs over a time range; inspect log-label values;
  retrieve CPU/memory/instance-count/connection/response/latency/bandwidth metrics
  (plan-dependent). Use these for "why did my deploy fail" and health summaries.
- **Env vars**: replace a service's environment variables (the main supported update
  operation). Treat values as secrets — don't echo them back unnecessarily.
- **Data**: list Render Postgres databases and run **read-only** SQL queries; list and
  inspect Key Value instances.

## Hard limits (say these plainly when relevant)

- No deleting services/databases, no manual deploy triggers, no scaling changes, no most
  other modifications — only env-var replacement on existing services.
- SQL is read-only; writes are rejected.
- Render API keys are broadly scoped; recommend a dedicated key and revoking it when done.

## Good default behaviors

- For "check my services" requests, produce a compact status table (name, type, status,
  last deploy) and flag anything not live.
- For "why did X fail", pull recent deploys → failed deploy details → filtered error logs,
  in that order, then summarize the root cause.
- For log/metric reads, start with a narrow time window (last 30–60 min) and widen only
  if needed.
- Billing note: creating paid instance types or databases can cost money — always confirm
  plan/region/spec with the user before create operations.
