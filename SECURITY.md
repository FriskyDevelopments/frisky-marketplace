# Secrets policy (frisky-marketplace is PUBLIC)

This repo is the public face of the Frisky MCP and plugins. Anything here is world-readable, including **PR titles, PR bodies, comments, issues and Actions logs**.

## Rule
**Secrets live in 1Password (vault `FriskyDev-Infra`) and are read at runtime** via `op run` / `op read` or a 1Password service account (`OP_SERVICE_ACCOUNT_TOKEN` set only in the runtime environment, never in the repo). Nothing else.

- Never commit `.env`, keys, tokens, passwords, or env dumps. Use `.env.example` with `op://` references or `<PLACEHOLDER>`.
- Never paste env output, logs with env, or `printenv` into a PR/issue/comment. Agents must not dump injected env into PR bodies.
- Install hooks: `pipx install pre-commit && pre-commit install`.
- CI `secret-scan` (gitleaks + trufflehog + PR-body check) must pass.
- If a secret leaks: rotate it first (Git and PR edit history keep the value), then redact, then record in fleet_shared (names only).

Repo settings to enable (owner): Secret scanning + Push protection (free on public repos), branch protection on `main` requiring `secret-scan`.
