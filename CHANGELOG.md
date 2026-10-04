# Marketplace release notes

User-facing marketplace updates are recorded here, newest first. The Kimi app
periodically refreshes this repository, so changes become available after they
reach the default branch and the app refreshes its index.

## Unreleased

### Added

- A central release-notes page for marketplace and connector updates.

## 2026-09-25

### Added

- [Magic Patterns](./magic-patterns) for UI prototyping, design exploration,
  and production code handoff. No action is required for existing plugins.
  ([source](https://github.com/FriskyDevelopments/frisky-marketplace/commit/dbc6369))

## 2026-09-24

### Added

- [Perplexity](./perplexity) for real-time web search, conversational AI, and
  reasoning. No action is required for existing plugins.
  ([source](https://github.com/FriskyDevelopments/frisky-marketplace/commit/52211d3))

### Changed

- Refreshed the marketplace README with a banner, plugin icons, and roster
  badges. Connector configuration did not change.
  ([source](https://github.com/FriskyDevelopments/frisky-marketplace/commit/150e07d))

## 2026-09-16

### Added

- [n8n connector](./n8n-connector) for searching and triggering workflows and
  working with executions and data tables. No action is required for existing
  plugins.
  ([source](https://github.com/FriskyDevelopments/frisky-marketplace/commit/2ad0487))

## Maintaining these notes

- Add user-facing marketplace or connector changes under **Unreleased** in the
  same pull request as the change.
- Use **Added**, **Changed**, **Fixed**, or **Removed** headings as needed.
- Link the affected plugin and explain what users can do differently.
- Call out setup, reauthorization, migrations, and breaking changes. State when
  no user action is required.
- When publishing an update, move its notes under a `YYYY-MM-DD` heading. Keep
  dated entries newest first and link the source pull request or commit.
- Never include credentials or private account details.

Plugin versions remain in each plugin's `kimi.plugin.json` manifest. These notes
cover recent updates rather than the repository's complete history.
