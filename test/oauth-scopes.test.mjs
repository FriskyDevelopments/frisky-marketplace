import assert from "node:assert/strict";
import test from "node:test";
import { validateMarketplace, validateScope } from "../scripts/oauth-scope-policy.mjs";

const root = new URL("..", import.meta.url).pathname;

test("every marketplace plugin passes the OAuth scope review", () => {
  assert.deepEqual(validateMarketplace(root), []);
});

test("broad and mutating scopes require explicit exceptions", () => {
  for (const scope of ["*", "all", "full_access", "admin", "org:admin", "event:write", "users_manage"]) {
    assert.match(validateScope(scope, { exceptions: {} }), /broad or mutating/);
  }
  assert.equal(validateScope("org:read", { exceptions: {} }), null);
});

test("offline access requires an explicit rationale", () => {
  assert.match(validateScope("offline_access", { exceptions: {} }), /documented exception/);
  assert.equal(
    validateScope("offline_access", { exceptions: { offline_access: "Required for refresh tokens." } }),
    null,
  );
});
