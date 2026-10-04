import { loadMarketplace, validateMarketplace } from "./oauth-scope-policy.mjs";

const root = process.cwd();
const errors = validateMarketplace(root);

if (errors.length > 0) {
  for (const error of errors) console.error(`fail ${error}`);
  process.exit(1);
}

const { policy } = loadMarketplace(root);
const oauthPlugins = Object.values(policy.plugins).filter((plugin) => plugin.auth === "oauth");
const scopeCount = oauthPlugins.reduce((total, plugin) => total + plugin.requestedScopes.length, 0);

console.log(`ok ${Object.keys(policy.plugins).length} plugins have OAuth reviews`);
console.log(`ok ${oauthPlugins.length} OAuth plugins request ${scopeCount} reviewed scopes`);
console.log("ok no unreviewed broad, write, admin, or offline scopes");
