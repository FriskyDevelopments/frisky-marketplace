# Permission Request — form

> **Status:** source definition only. Tally has no plugin or connector right now, so no live
> Tally form exists. `form.json` is the machine-readable source; publish it to Tally or an
> equivalent once a credential-free route exists.

## When to file

Only for **critical work**:

- the action **costs money**, or
- the action needs **access beyond what the agent already has**.

Everything else is done without a form. **No form, no command:** the command runs only
after Frisky marks the request **Approve**. Vague entries are rejected.

Never put secret values in the form.

## Agent fills in (all required)

| Field | What to write |
|---|---|
| Agent name | Who is asking |
| Exact action | The exact command or operation |
| Exact target | The specific repo / account / product ID / URL / server |
| Why it can't wait | The concrete consequence of waiting |
| Cost | Money (amount + currency) and/or the exact new access needed |

## Frisky fills in

| Field | Values |
|---|---|
| Decision | **Approve** or **Reject** (required) |
| Note | Optional |
