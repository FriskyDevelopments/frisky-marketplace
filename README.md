<div align="center">

<pre>
███████╗██████╗ ██╗███████╗██╗  ██╗██╗   ██╗
██╔════╝██╔══██╗██║██╔════╝██║ ██╔╝╚██╗ ██╔╝
█████╗  ██████╔╝██║███████╗█████╔╝  ╚████╔╝
██╔══╝  ██╔══██╗██║╚════██║██╔═██╗   ╚██╔╝
██║     ██║  ██║██║███████║██║  ██╗   ██║
╚═╝     ╚═╝  ╚═╝╚═╝╚══════╝╚═╝  ╚═╝   ╚═╝
        M A R K E T P L A C E
</pre>

<span style="color:#00e5ff">eight connectors · one org tab · zero ceremony</span>

</div>

---

Personal plugin marketplace for the **Kimi** app. Add this repo in the
Directory's **Organization** tab — the app re-fetches it periodically, so
every push here is a release.

## The Roster

| # | Plugin | What it wires into your chats |
|---|--------|-------------------------------|
| 01 | **sentry-connector** | Sentry's official MCP — errors, issues, traces, replays, release health |
| 02 | **composio-connector** | Composio's hosted tool router — 1000+ apps behind one OAuth |
| 03 | **convex-connector** | Convex backend — projects, deployments, data |
| 04 | **friskydev-mcp** | FriskyDev gateway — 15 specialist operators + shared memory |
| 05 | **render** | Render.com — services, deploys, logs, cron jobs |
| 06 | **framer** | Framer — pages, CMS collections, publish |
| 07 | **chatprd** | ChatPRD — product docs on demand |
| 08 | **folios** | Folios — evidence workspaces, playbooks |

| 09 | **cloudflare-connector** | Cloudflare official MCP — Workers, Pages, KV, D1, R2, DNS, Zero Trust, Analytics |

| 10 | **n8n-connector** | Your self-hosted n8n instance MCP — workflows, executions, data tables |

## Install

1. Open the Kimi app → **Directory** → **Organization** tab
2. Paste this repo's URL:
   `https://github.com/FriskyDevelopments/frisky-marketplace`
3. Install plugins from the org marketplace as they appear

## Publish a New Plugin

```bash
# 1. drop the plugin folder at the repo root
cp -R ~/path/to/my-plugin ./my-plugin

# 2. add one entry to plugins.json
#    { "name": "my-plugin", "path": "./my-plugin", ... }

# 3. push — the app picks it up on its next fetch
git add -A && git commit -m "add my-plugin" && git push
```

`plugins.json` is the native Kimi index — entries point at in-repo folders
(`path`) or external repos (`url`), with optional `description`, `category`,
and `owner` metadata.

## Layout

```
frisky-marketplace/
├── plugins.json        ← the index (name: "frisky")
├── README.md
└── <plugin>/           ← one folder per plugin, each with kimi.plugin.json
```

---

<div align="center">
<sub>frisky developments · wired for <span style="color:#ff2ea6">friskypup</span></sub>
</div>
