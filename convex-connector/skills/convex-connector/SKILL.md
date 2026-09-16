---
name: convex-connector
description: 连接你的 Convex 项目。当用户提到 Convex（convex.dev 后端平台）、想查看 Convex 部署状态、浏览数据表、查询/检查表数据、运行 Convex 函数（query/mutation/action）、查看函数日志与性能洞察（insights）、或查看/设置/删除 Convex 环境变量时，使用本技能。触发词：convex、convex dev、convex deployment、convex 数据表、convex 环境变量、convex logs。
---

# Convex Connector

通过 Convex 官方 CLI（`convex` npm 包 ≥ 1.40）**内置的 MCP server**（`convex mcp start`，Beta）把用户的 Convex 项目暴露为 MCP 工具。本插件已在 `kimi.plugin.json` 里声明该 stdio MCP server（`npx -y convex@1.45.0 mcp start`），安装后工具直接可用，不需要再手工起服务。

## 前置条件

1. **Node.js + npx** 可用（MCP server 通过 `npx` 启动，首次运行会自动下载 convex 包）。
2. **已登录 Convex**：在用户的 Convex 项目目录里跑过一次 `npx convex dev` 或 `npx convex login`（本机已有 Convex 凭据 ~/.convex）。没有凭据时工具调用会报认证错误——提示用户先在项目目录执行 `npx convex login`。
3. **多项目模式**：插件默认不传 `--project-dir`，MCP server 可同时服务多个项目，每次工具调用需指定项目目录（用户的 Convex 项目路径）。如果用户只有一个项目，也可以在其项目目录下使用。

## 可用工具（convex mcp start 提供）

| 工具 | 作用 | 读写 |
|---|---|---|
| `status` | 查看部署状态 | 只读 |
| `tables` | 列出某部署的所有表（含推断/声明的 schema） | 只读 |
| `data` | 浏览/检查表数据 | 只读 |
| `runOneoffQuery` | 对部署执行一次性 Convex 查询 | 只读 |
| `run` | 运行指定的 Convex 函数（query/mutation/action） | 可能写 |
| `functionSpec` | 查看函数签名/规格 | 只读 |
| `logs` | 查看函数日志 | 只读 |
| `insights` | 性能洞察（慢查询等） | 只读 |
| `envList` / `envGet` | 列出 / 读取环境变量 | 只读 |
| `envSet` / `envRemove` | 设置 / 删除环境变量 | **写** |

## 使用流程

1. 确认用户的目标 Convex 项目目录（问路径，或从对话上下文推断）。
2. 先用只读工具建立上下文：`status` 看部署 → `tables` 看表 → `data` / `runOneoffQuery` 取数。
3. 排障时：`logs` 看日志、`insights` 看性能问题。
4. 返回结果给用户时保持摘要式输出，不要把大段原始 JSON 全部贴出。

## 安全红线

- **写操作必须先向用户确认**：`run`（运行 mutation/action）、`envSet`、`envRemove` 在调用前把「动作 + 目标部署/函数/变量名」复述给用户，取得明确同意后再执行。
- **生产环境保护**：MCP server 默认不触碰生产部署（读写都不允许）。如果用户明确要求对生产环境操作，需要重启 MCP server 并加 `--cautiously-allow-production-pii`（只读）或 `--dangerously-enable-production-deployments`（含写）——修改插件的 `kimi.plugin.json` 里 mcpServers 的 args 后重新安装。务必向用户说明这两个 flag 的风险，PII 泄露与生产数据变更不可逆。
- **环境变量是敏感信息**：`envGet`/`envList` 的结果只摘要展示（变量名 + 是否有值），不要把值原文贴进对话。

## 故障排查

- 工具报认证/登录错误 → 让用户在项目目录跑 `npx convex login`。
- 工具报找不到部署/项目 → 确认传对了项目目录（多项目模式下每个工具调用都要指定）。
- `npx` 启动慢或失败 → 检查 Node.js 版本（建议 ≥ 18）与网络；可改为本地预装 `npm i -g convex` 后把 manifest 里 command 改成 `convex`。
- 个别工具想禁用 → 在 mcpServers args 里加 `--disable-tools <逗号分隔的工具名>`。
