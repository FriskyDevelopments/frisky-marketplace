import fs from "node:fs";
import path from "node:path";

const SCOPE_PATTERN = /^[A-Za-z0-9:._~+-]+$/;
const WRITE_OR_ADMIN = /(?:^|[:._-])(write|admin)(?:$|[:._-])/i;
const EXACT_DENY = new Set([
  "*",
  "all",
  "admin",
  "full",
  "full_access",
  "private_metadata",
  "public_metadata",
]);

export function uniqueSorted(values) {
  return [...new Set(values)].sort((a, b) => a.localeCompare(b));
}

export function scopeDenial(scope, entry) {
  if (typeof scope !== "string" || scope.length === 0) {
    return "scope must be a non-empty string";
  }
  if (!SCOPE_PATTERN.test(scope) || scope.includes("*")) {
    return `scope ${JSON.stringify(scope)} is not a single concrete token`;
  }
  if (EXACT_DENY.has(scope.toLowerCase())) {
    return `scope ${scope} is denied`;
  }
  if (WRITE_OR_ADMIN.test(scope) && entry.allowWriteScopes !== true) {
    return `scope ${scope} is a write or admin scope and this plugin does not allow them`;
  }
  if (scope === "offline_access" && entry.allowOfflineAccess !== true) {
    return "offline_access is not allowed for this plugin";
  }
  return null;
}

function sameSet(left, right) {
  const a = uniqueSorted(left);
  const b = uniqueSorted(right);
  return a.length === b.length && a.every((value, index) => value === b[index]);
}

export function manifestServer(manifest) {
  const servers = manifest.mcpServers;
  if (!servers || typeof servers !== "object") return null;
  const names = Object.keys(servers);
  if (names.length === 0) return null;
  return { name: names[0], config: servers[names[0]], names };
}

export function declaredManifestScopes(config) {
  if (!config || typeof config !== "object") return [];
  const found = [];
  if (Array.isArray(config.scopes)) found.push(...config.scopes);
  if (typeof config.scope === "string") found.push(...config.scope.split(/\s+/));
  const oauth = config.oauth;
  if (oauth && typeof oauth === "object") {
    if (Array.isArray(oauth.scopes)) found.push(...oauth.scopes);
    if (typeof oauth.scopes === "string") found.push(...oauth.scopes.split(/\s+/));
    if (typeof oauth.scope === "string") found.push(...oauth.scope.split(/\s+/));
  }
  return found.filter((scope) => typeof scope === "string" && scope.length > 0);
}

export function loadMarketplace(root) {
  const index = JSON.parse(fs.readFileSync(path.join(root, "plugins.json"), "utf8"));
  const plugins = index.plugins.map((entry) => {
    const manifestPath = path.join(root, entry.path, "kimi.plugin.json");
    const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
    return { index: entry, manifest, manifestPath };
  });
  const policy = JSON.parse(fs.readFileSync(path.join(root, "oauth-scopes.json"), "utf8"));
  return { index, plugins, policy };
}

function push(errors, plugin, message) {
  errors.push(`${plugin}: ${message}`);
}

export function validateEntry(name, entry, manifest) {
  const errors = [];
  if (!entry || typeof entry !== "object") {
    push(errors, name, "missing oauth-scopes.json entry");
    return errors;
  }
  if (!Array.isArray(entry.requestedScopes)) {
    push(errors, name, "requestedScopes must be an array");
    return errors;
  }
  const requested = entry.requestedScopes;
  if (uniqueSorted(requested).join("\n") !== requested.join("\n")) {
    push(errors, name, "requestedScopes must be unique and sorted");
  }
  for (const scope of requested) {
    const denial = scopeDenial(scope, entry);
    if (denial) push(errors, name, denial);
  }

  const server = manifestServer(manifest);
  if (entry.auth === "none") {
    if (server) push(errors, name, "auth none but the manifest declares an MCP server");
    if (requested.length !== 0) push(errors, name, "auth none cannot request scopes");
    return errors;
  }
  if (!server) {
    push(errors, name, "manifest is missing mcpServers");
    return errors;
  }
  if (server.names.length !== 1) {
    push(errors, name, "expected exactly one mcpServers entry");
  }
  if (manifest.name !== name) {
    push(errors, name, `manifest name ${manifest.name} does not match plugins.json`);
  }

  const declared = declaredManifestScopes(server.config);
  if (declared.length > 0 && !sameSet(declared, requested)) {
    push(
      errors,
      name,
      `manifest scopes [${uniqueSorted(declared).join(", ")}] differ from requestedScopes [${requested.join(", ")}]`,
    );
  }

  if (entry.auth === "oauth") {
    if (typeof server.config.url !== "string" || server.config.url !== entry.serverUrl) {
      push(errors, name, `serverUrl must match manifest url ${server.config.url ?? "(none)"}`);
    }
    if (requested.length === 0 && entry.emptyScopeRequestReviewed !== true) {
      push(errors, name, "oauth plugin requests no scopes; set emptyScopeRequestReviewed after an audit");
    }
  } else if (entry.auth === "api-key" || entry.auth === "local-cli") {
    if (requested.length !== 0) {
      push(errors, name, `${entry.auth} plugin cannot request OAuth scopes`);
    }
    if (entry.auth === "api-key" && entry.serverUrl && server.config.url && server.config.url !== entry.serverUrl) {
      push(errors, name, "serverUrl does not match the manifest");
    }
    if (entry.auth === "local-cli" && typeof server.config.command !== "string") {
      push(errors, name, "local-cli plugin must use a stdio command");
    }
  } else {
    push(errors, name, `unknown auth ${JSON.stringify(entry.auth)}`);
  }

  if (Array.isArray(entry.protectedResourceScopes)) {
    const outside = requested.filter((scope) => !entry.protectedResourceScopes.includes(scope));
    if (outside.length > 0 && entry.protectedResourceScopes.length > 0) {
      push(errors, name, `requested scopes outside the protected resource: ${outside.join(", ")}`);
    }
    if (uniqueSorted(entry.protectedResourceScopes).join("\n") !== entry.protectedResourceScopes.join("\n")) {
      push(errors, name, "protectedResourceScopes must be unique and sorted");
    }
  }
  if (Array.isArray(entry.authorizationServerScopesReviewed)) {
    const outside = requested.filter((scope) => !entry.authorizationServerScopesReviewed.includes(scope));
    if (outside.length > 0) {
      push(errors, name, `requested scopes outside the reviewed authorization server list: ${outside.join(", ")}`);
    }
  }
  if (typeof entry.reason !== "string" || entry.reason.trim().length < 20) {
    push(errors, name, "reason must explain the least-privilege decision");
  }
  return errors;
}

export function validateMarketplace(root) {
  const { plugins, policy } = loadMarketplace(root);
  const errors = [];
  if (policy.version !== 1) errors.push("oauth-scopes.json version must be 1");
  const names = plugins.map((plugin) => plugin.index.name);
  const policyNames = Object.keys(policy.plugins ?? {});
  for (const name of names) {
    if (!policy.plugins?.[name]) push(errors, name, "missing oauth-scopes.json entry");
  }
  for (const name of policyNames) {
    if (!names.includes(name)) push(errors, name, "policy entry has no plugins.json plugin");
  }
  for (const plugin of plugins) {
    errors.push(...validateEntry(plugin.index.name, policy.plugins?.[plugin.index.name], plugin.manifest));
  }
  return errors;
}

export function compareDiscovery(entry, discovery) {
  const errors = [];
  const requested = entry.requestedScopes ?? [];
  const liveResource = discovery.protectedResourceScopes;
  if (Array.isArray(liveResource)) {
    const reviewed = entry.protectedResourceScopes ?? [];
    if (!sameSet(liveResource, reviewed)) {
      errors.push(
        `protected-resource scopes drifted: live [${uniqueSorted(liveResource).join(", ")}] reviewed [${reviewed.join(", ")}]`,
      );
    }
    if (liveResource.length > 0) {
      const outside = requested.filter((scope) => !liveResource.includes(scope));
      if (outside.length > 0) {
        errors.push(`requested scopes are not in the protected-resource list: ${outside.join(", ")}`);
      }
    }
  }
  if (
    Array.isArray(entry.authorizationServerScopesReviewed) &&
    Array.isArray(discovery.authorizationServerScopes) &&
    (entry.protectedResourceScopes ?? []).length === 0
  ) {
    if (!sameSet(discovery.authorizationServerScopes, entry.authorizationServerScopesReviewed)) {
      errors.push(
        `authorization-server scopes drifted: live [${uniqueSorted(discovery.authorizationServerScopes).join(", ")}] reviewed [${entry.authorizationServerScopesReviewed.join(", ")}]`,
      );
    }
  }
  for (const scope of requested) {
    const denial = scopeDenial(scope, entry);
    if (denial) errors.push(denial);
  }
  return errors;
}
