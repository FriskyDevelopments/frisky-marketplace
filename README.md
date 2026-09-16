# Frisky Marketplace
Personal Kimi plugin marketplace (org tab). Index: `plugins.json` (native Kimi format).
## Plugins

| Plugin | Category | Description |
|---|---|---|
| [chatprd](./chatprd) | PRODUCTIVITY | ChatPRD MCP connector — push PRDs, feature specs and FriskyClaw ops digests into ChatPRD via OAuth (no API key) |
| [composio-connector](./composio-connector) | PRODUCTIVITY | 连接 Composio 托管 MCP 服务，通过一个端点调用 1000+ 应用的托管工具（Gmail、Slack、Notion、Linear、HubSpot 等），Composio 统一管理 OAuth 授权 |
| [convex-connector](./convex-connector) | DEVELOPER_TOOLS | 连接你的 Convex 项目：通过官方 convex CLI 内置的 MCP server（convex mcp start，Beta）查看部署状态、浏览数据表、查询数据、运行函数、查看日志与性能洞察、管理环境变量。 |
| [folios](./folios) | PRODUCTIVITY | Folios — espacio de trabajo inteligente de evidencia / intelligent proof workspace. ES: Folios reúne tu material de trabajo, lo conecta con tu intención y lo convierte en folios estructurados y compartibles. Organiza tus flujos de trabajo como Playbooks —investigación de mercado, pitch a inversionistas, QBR, video con IA, traducción de PDF y más— con experiencia bilingüe: español (México) como idioma principal y English (US) como segundo idioma, para equipos que trabajan entre México y EE. UU. Diseño Editorial Workbench con ambición de nivel Awwwards: tipografía expresiva, motion con propósito, composición editorial asimétrica. EN: Folios collects your working material, connects it to your intent, and turns it into structured, shareable folios. Organize your workflows as Playbooks — market research, investor pitch, QBR, AI video, PDF translation, and more — with a bilingual experience: Spanish (Mexico) as the primary language and English (US) as a user-controlled second locale for teams working across Mexico and the United States. Editorial Workbench design with Awwwards-level ambition: expressive typography, purposeful motion, asymmetric editorial composition. |
| [framer](./framer) | PRODUCTIVITY | Diseña, edita y publica sitios web en Framer desde Kimi: lee páginas y contexto del proyecto, gestiona colecciones CMS, aplica cambios, previsualiza y publica/despliega con el MCP de Framer (framer-mcp-server vía npx). |
| [friskydev-mcp](./friskydev-mcp) | PRODUCTIVITY | Boutique AI operator infrastructure — 15 specialists, unified MongoDB memory, deployable MCP surface for ChatGPT, Codex & AI workers. Cyberpunk clarity without dashboard clutter. |
| [render](./render) | DEVTOOLS | Manage Render cloud infrastructure with Render's official MCP server: list workspaces and services, create web services, static sites, cron jobs, Postgres databases and Key Value stores, inspect deploys, read logs and metrics, update env vars, and run read-only SQL on Render Postgres. |
| [sentry-connector](./sentry-connector) | DEVELOPER_TOOLS | 连接 Sentry 官方 MCP 服务，查询错误、issue、事件、release、trace、session replay 等监控数据 |

## Usage

Paste this repo's URL into the Kimi app Directory → Organization tab
(git repositories or hosted marketplace.json URLs). The app re-fetches periodically.
Drop a new plugin folder + `plugins.json` entry and push to publish.
