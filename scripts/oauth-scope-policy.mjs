import { readFileSync } from "node:fs";
import { join } from "node:path";

const AUTH_TYPES = new Set(["api-key", "local-cli", "none", "oauth"]);
const BROAD_SCOPE = /(^|[:._-])(admin|manage|write)($|[:._-])|^(all|\*|full_access)$/i;

function readJson(path) {
  return JSON.parse(readFileSync(path, "utf8"));
}

function sortedUnique(values) {
  return [...new Set(values)].sort();
}

function add(errors, plugin, message) {
  errors.push(`${plugin}: ${message}`);
}

export function validateScope(scope, entry) {
  if (scope === "offline_access" && !entry.exceptions?.offline_access) {
    return "offline_access requires a documented exception";
  }
  if (BROAD_SCOPE.test(scope) && !entry.exceptions?.[scope]) {
    return `${scope} is a broad or mutating scope without a documented exception`;
  }
  return null;
}

export function loadMarketplace(root) {
  const index = readJson(join(root, "plugins.json"));
  const policy = readJson(join(root, "oauth-scopes.json"));
  const plugins = index.plugins.map((plugin) => ({
    index: plugin,
    manifest: readJson(join(root, plugin.path, "kimi.plugin.json")),
  }));
  return { plugins, policy };
}

export function validateMarketplace(root) {
  const { plugins, policy } = loadMarketplace(root);
  const errors = [];
  const indexedNames = plugins.map(({ index }) => index.name).sort();
  const reviewedNames = Object.keys(policy.plugins ?? {}).sort();

  if (policy.version !== 1) errors.push("oauth-scopes.json: version must be 1");
  if (!/^\d{4}-\d{2}-\d{2}$/.test(policy.auditedOn ?? "")) {
    errors.push("oauth-scopes.json: auditedOn must use YYYY-MM-DD");
  }
  if (indexedNames.join("\n") !== reviewedNames.join("\n")) {
    errors.push("oauth-scopes.json: reviews must exactly cover plugins.json");
  }

  for (const { index, manifest } of plugins) {
    const name = index.name;
    const entry = policy.plugins?.[name];
    if (!entry) continue;
    if (!AUTH_TYPES.has(entry.auth)) add(errors, name, `unknown auth type ${entry.auth}`);
    if (!Array.isArray(entry.requestedScopes)) {
      add(errors, name, "requestedScopes must be an array");
      continue;
    }
    if (entry.requestedScopes.some((scope) => typeof scope !== "string" || !scope)) {
      add(errors, name, "requestedScopes must contain non-empty strings");
    }
    if (entry.requestedScopes.join("\n") !== sortedUnique(entry.requestedScopes).join("\n")) {
      add(errors, name, "requestedScopes must be sorted and unique");
    }
    if (entry.auth !== "oauth" && entry.requestedScopes.length > 0) {
      add(errors, name, `${entry.auth} plugins cannot request OAuth scopes`);
    }
    if (entry.auth === "oauth" && !entry.serverUrl) {
      add(errors, name, "OAuth plugins must record their serverUrl");
    }

    const servers = Object.values(manifest.mcpServers ?? {});
    const hostedServer = servers.find((server) => typeof server.url === "string");
    if (entry.serverUrl && hostedServer?.url !== entry.serverUrl) {
      add(errors, name, "serverUrl does not match the plugin manifest");
    }
    if (entry.auth === "local-cli" && !servers.some((server) => typeof server.command === "string")) {
      add(errors, name, "local-cli review does not match the plugin manifest");
    }
    if (entry.auth === "none" && servers.length > 0) {
      add(errors, name, "auth none is invalid for a plugin with an MCP server");
    }

    for (const scope of entry.requestedScopes) {
      const error = validateScope(scope, entry);
      if (error) add(errors, name, error);
    }
    if (typeof entry.reason !== "string" || entry.reason.trim().length < 40) {
      add(errors, name, "reason must document the least-privilege decision");
    }

    const serializedManifest = JSON.stringify(manifest);
    if (/"(?:oauth_?)?scopes?"\s*:/i.test(serializedManifest)) {
      add(errors, name, "manifest contains an unreviewed inline OAuth scope field");
    }
  }
  return errors;
}
