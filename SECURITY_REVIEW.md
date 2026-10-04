# New Plugin Security Review

Complete this checklist for every new plugin before it is added to the
marketplace. Copy the checklist into the pull request description, link any
supporting evidence, and leave items unchecked when they need follow-up.
Publication is blocked until every applicable item is checked by the author
and confirmed by a reviewer.

## Source and ownership

- [ ] The plugin name, owner, source repository, and license are identified.
- [ ] The plugin and each MCP server come from the expected publisher. Any
      third-party or community-maintained component is called out explicitly.
- [ ] Remote URLs use HTTPS and point to the intended host. Redirects and
      look-alike domains have been checked.
- [ ] Executable packages, container images, actions, and other dependencies
      are pinned to a reviewed version or immutable digest where supported.

## Authentication and permissions

- [ ] Requested OAuth scopes, API permissions, filesystem access, and network
      access are documented and limited to what the plugin needs.
- [ ] Read-only access is used where write access is not required.
- [ ] Credentials are supplied through OAuth, environment variables, or the
      host application's secret storage. No token, key, password, cookie, or
      other secret is committed in the plugin files or examples.
- [ ] Authentication failure and credential revocation do not expose secrets
      or leave the plugin with unintended access.

## Data handling

- [ ] The data sent to each external service is documented, including prompts,
      files, repository content, account data, and telemetry.
- [ ] Sensitive data is minimized, encrypted in transit, and not retained or
      logged beyond the stated need.
- [ ] The plugin does not transmit data to undeclared endpoints.
- [ ] User-facing instructions disclose consequential data access and any
      relevant retention or deletion behavior.

## Tools and untrusted input

- [ ] Every exposed tool has been reviewed for destructive or externally
      visible actions such as deleting data, deploying, publishing, messaging,
      purchasing, or changing permissions.
- [ ] Consequential actions require clear user intent and confirmation where
      the action is difficult to reverse.
- [ ] Tool arguments and remote responses are treated as untrusted input.
      Inputs are validated, and shell, path, URL, and prompt injection risks
      are mitigated.
- [ ] Tool names and descriptions accurately state their effects and do not
      encourage bypassing host security controls.

## Verification and approval

- [ ] `kimi.plugin.json` contains only expected servers, commands, arguments,
      URLs, and environment-variable names.
- [ ] Installation and a representative read-only operation were tested in a
      non-production account or environment.
- [ ] Any write-capable or destructive operation was tested safely, or the
      reason it was not tested is documented in the pull request.
- [ ] The plugin can be removed and its access revoked without leaving active
      credentials or unexpected resources.
- [ ] An independent reviewer compared this checklist with the plugin diff and
      confirmed all exceptions or residual risks in the pull request.

## Review record

- Plugin:
- Source and version:
- Reviewer:
- Review date:
- Exceptions or residual risks:
