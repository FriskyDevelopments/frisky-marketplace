# Marketplace release notes

User-facing updates to the Frisky marketplace are recorded here, newest first.
The Kimi app periodically re-fetches the marketplace; an update becomes available
after it reaches the repository's default branch and the app refreshes its index.
Plugin versions remain in each plugin's `kimi.plugin.json` manifest.

## Unreleased

### Added
- A central release-notes page linked from the README.

## 2026-09-25

### Added
- [Magic Patterns](./magic-patterns): prototype UI, generate design directions,
  and hand off production code. No changes to existing plugin installations.
  ([source](https://github.com/FriskyDevelopments/frisky-marketplace/commit/dbc6369))

## 2026-09-24

### Added
- [Perplexity](./perplexity): real-time web search, conversational AI, and
  reasoning through the hosted MCP connector. No changes to existing plugin
  installations.
  ([source](https://github.com/FriskyDevelopments/frisky-marketplace/commit/52211d3))

### Changed
- Refreshed the README with a marketplace banner, plugin icons, and roster badges.
  This was a documentation update; connector configuration was unchanged.
  ([source](https://github.com/FriskyDevelopments/frisky-marketplace/commit/150e07d))

## 2026-09-16

### Added
- [n8n connector](./n8n-connector): connect a self-hosted n8n instance to search
  and trigger workflows and work with executions and data tables. No changes to
  existing plugin installations.
  ([source](https://github.com/FriskyDevelopments/frisky-marketplace/commit/2ad0487))

## Maintaining these notes

- Include user-facing marketplace or connector changes under **Unreleased** in
  the same PR as the update. Use **Added**, **Changed**, **Fixed**, or **Removed**
  headings as needed; omit empty headings.
- Name and link the affected plugin, explain what users can do differently, and
  state any required setup, reauthorization, or migration steps. Explicitly call
  out breaking changes; if no user action is needed, say so.
- When preparing an update for the default branch, move its notes into a
  `YYYY-MM-DD` heading using the release date (combine updates on the same date).
  Keep pending changes under **Unreleased** and dated entries newest first.
- Link a source commit or PR when available. Do not include credentials or
  private account details in release notes.

These notes cover recent updates, not a complete backfill of repository history.
