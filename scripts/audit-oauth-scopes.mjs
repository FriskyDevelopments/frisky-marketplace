import { compareDiscovery, loadMarketplace, validateMarketplace } from "./oauth-scope-policy.mjs";

const root = process.cwd();
const live = process.argv.includes("--live");

function wellKnownUrls(serverUrl) {
  const parsed = new URL(serverUrl);
  const origin = `${parsed.protocol}//${parsed.host}`;
  const pathname = parsed.pathname.replace(/\/$/, "");
  const urls = [];
  if (pathname) urls.push(`${origin}/.well-known/oauth-protected-resource${pathname}`);
  urls.push(`${origin}/.well-known/oauth-protected-resource`);
  return urls;
}

async function readJson(url) {
  const response = await fetch(url, {
    headers: { accept: "application/json", "user-agent": "frisky-oauth-scope-audit/1.0" },
    redirect: "follow",
  });
  if (!response.ok) {
    const error = new Error(`HTTP ${response.status} for ${url}`);
    error.status = response.status;
    throw error;
  }
  const contentType = response.headers.get("content-type") ?? "";
  if (!contentType.includes("json")) {
    throw new Error(`non-JSON response for ${url}`);
  }
  return response.json();
}

async function discoverProtectedResource(serverUrl) {
  let lastError = null;
  for (const url of wellKnownUrls(serverUrl)) {
    try {
      const body = await readJson(url);
      if (body && (body.resource || body.authorization_servers || body.scopes_supported)) {
        return { url, body };
      }
    } catch (error) {
      lastError = error;
    }
  }
  throw lastError ?? new Error(`no protected-resource metadata for ${serverUrl}`);
}

async function discoverAuthorizationServer(metadata) {
  const issuer = Array.isArray(metadata.authorization_servers) ? metadata.authorization_servers[0] : null;
  if (!issuer) return null;
  const url = `${issuer.replace(/\/$/, "")}/.well-known/oauth-authorization-server`;
  try {
    const body = await readJson(url);
    return { url, body };
  } catch {
    return null;
  }
}

function scopesOf(body) {
  if (!body || !Array.isArray(body.scopes_supported)) return [];
  return body.scopes_supported.filter((scope) => typeof scope === "string");
}

async function auditLive(policy) {
  const errors = [];
  for (const [name, entry] of Object.entries(policy.plugins)) {
    if (!entry.serverUrl) continue;
    if (entry.auth !== "oauth" && entry.auth !== "api-key") continue;
    try {
      const resource = await discoverProtectedResource(entry.serverUrl);
      const authorization = await discoverAuthorizationServer(resource.body);
      const discovery = {
        protectedResourceScopes: scopesOf(resource.body),
        authorizationServerScopes: authorization ? scopesOf(authorization.body) : null,
      };
      const entryErrors = compareDiscovery(entry, discovery);
      if (entryErrors.length === 0) {
        const extra =
          discovery.authorizationServerScopes && discovery.authorizationServerScopes.length > discovery.protectedResourceScopes.length
            ? ` (authorization server advertises ${discovery.authorizationServerScopes.length} scopes)`
            : "";
        console.log(`ok  ${name}: ${entry.requestedScopes.join(" ") || "(none)"}${extra}`);
      } else {
        for (const message of entryErrors) errors.push(`${name}: ${message}`);
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      if (entry.liveProbe === "skip") {
        console.log(`skip ${name}: ${message}`);
        continue;
      }
      errors.push(`${name}: live discovery failed: ${message}`);
    }
  }
  return errors;
}

const staticErrors = validateMarketplace(root);
if (staticErrors.length > 0) {
  for (const error of staticErrors) console.error(`fail ${error}`);
  process.exit(1);
}
console.log(`ok  static policy matches ${Object.keys(loadMarketplace(root).policy.plugins).length} plugins`);

if (!live) {
  console.log("static check only; re-run with --live to compare protected-resource metadata");
  process.exit(0);
}

const { policy } = loadMarketplace(root);
const liveErrors = await auditLive(policy);
if (liveErrors.length > 0) {
  for (const error of liveErrors) console.error(`fail ${error}`);
  process.exit(1);
}
console.log("ok  live protected-resource scopes match the review");
