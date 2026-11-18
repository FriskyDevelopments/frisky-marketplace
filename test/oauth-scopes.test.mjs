import assert from "node:assert/strict";
import test from "node:test";
import { compareDiscovery, scopeDenial, validateMarketplace } from "../scripts/oauth-scope-policy.mjs";

const root = new URL("..", import.meta.url).pathname;

test("marketplace oauth scope policy matches every plugin", () => {
  const errors = validateMarketplace(root);
  assert.deepEqual(errors, []);
});

test("write, admin, wildcard, and metadata scopes are denied", () => {
  const entry = { allowWriteScopes: false, allowOfflineAccess: false };
  for (const scope of ["*", "all", "admin", "full_access", "private_metadata", "public_metadata", "event:write", "workers-scripts.write", "dns.write", "connectivity-directory.admin", "offline_access"]) {
    assert.equal(typeof scopeDenial(scope, entry), "string", scope);
  }
  assert.equal(scopeDenial("org:read", entry), null);
  assert.equal(scopeDenial("account:read", entry), null);
  assert.equal(scopeDenial("offline_access", { ...entry, allowOfflineAccess: true }), null);
});

test("a cloudflare-style authorization catalog cannot widen the request", () => {
  const entry = {
    requestedScopes: ["account:read", "user:read", "workers-scripts.write"],
    protectedResourceScopes: ["account:read", "user:read"],
    allowWriteScopes: true,
    allowOfflineAccess: false,
  };
  const errors = compareDiscovery(entry, {
    protectedResourceScopes: ["account:read", "user:read"],
    authorizationServerScopes: ["account:read", "user:read", "dns.write", "workers-scripts.write"],
  });
  assert.ok(errors.some((error) => error.includes("workers-scripts.write")));
});

test("protected-resource drift fails the live comparison", () => {
  const entry = {
    requestedScopes: ["org:read"],
    protectedResourceScopes: ["alerts:write", "event:write", "org:read", "project:write", "team:write"],
    allowWriteScopes: false,
    allowOfflineAccess: false,
  };
  const errors = compareDiscovery(entry, {
    protectedResourceScopes: ["alerts:write", "event:write", "org:admin", "org:read", "project:write", "team:write"],
    authorizationServerScopes: null,
  });
  assert.ok(errors.some((error) => error.includes("drifted")));
  assert.equal(scopeDenial("org:admin", entry) !== null, true);
});

test("chatprd cannot pick up clerk private_metadata from the authorization server", () => {
  const entry = {
    requestedScopes: ["email", "private_metadata", "profile"],
    protectedResourceScopes: ["email", "profile"],
    allowWriteScopes: false,
    allowOfflineAccess: false,
  };
  const errors = compareDiscovery(entry, {
    protectedResourceScopes: ["email", "profile"],
    authorizationServerScopes: ["email", "offline_access", "openid", "private_metadata", "profile", "public_metadata", "user:org:read"],
  });
  assert.ok(errors.some((error) => error.includes("private_metadata")));
});
