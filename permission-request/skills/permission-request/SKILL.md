---
name: permission-request
description: Use before any action that costs money or needs access beyond what the agent already has. Defines the fleet rule "no form, no command" and the permission-request form Frisky approves or rejects. Triggers on "permission request", "approval form", "needs Frisky's approval", "costs money", "new access".
---

# Permission Request

## The rule

1. File a permission request **only for critical work**: an action that **costs money** or
   **needs access beyond what you already have**.
2. Everything else: just do it. No form.
3. **No form, no command.** A critical action runs only after Frisky marks the request
   **Approve**. Reject or no answer means it does not run.
4. Be exact. Vague entries get rejected.
5. Never write secret values into a request.

## Required fields

Agent name, exact action, exact target, why it can't wait, cost (money or new access).
Frisky adds the decision (Approve / Reject) and an optional note.

Full definition: `../../form.json` (machine-readable) and `../../FORM.md` (readable).

## Current status

Tally has no plugin or connector right now, so there is no live Tally form yet. Until one
is published through a credential-free route, submit the same fields to Frisky in writing
and wait for an explicit Approve.
