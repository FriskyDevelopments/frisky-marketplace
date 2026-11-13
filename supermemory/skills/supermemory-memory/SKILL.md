---
name: supermemory-memory
description: "Use when the user wants to search, save, organize or review memories in Supermemory, the persistent memory and knowledge layer. Covers recalling prior decisions and preferences, storing new facts, updating the user profile, managing spaces and container tags, and forgetting stale memories. Trigger on: remember this, what do you know about me, search my memory, memory, Supermemory, recall my preferences."
---

# Supermemory Memory Operations

Supermemory is the persistent memory and knowledge layer behind this session. The MCP server named
`"supermemory"` exposes the full tool set; the Agent calls the tools directly.

## Recall before you assume

Search memory whenever the answer depends on something that happened outside the current
conversation: a past decision, a stated preference, an architecture choice, a convention, a person,
a dead end already explored.

1. Form a specific query from the user's actual situation, not a generic keyword.
2. Call `search_memory` and read the returned documents.
3. If the results are close but not exact, call `get_profile` for the stable facts and
   `list_documents` for the longer record.
4. Treat recalled content as prior context to verify, not as current truth. The user may have
   changed their mind since it was stored.

Do not skip the search just because the current thread looks self-contained. The whole point of the
memory layer is that the answer is often in a session that already ended.

## Save what is worth keeping

Store a memory when it will still matter later:

- decisions and their reasons, especially the reason a rejected option was rejected;
- stated preferences, corrections, and "always do it this way" instructions;
- architecture and stack facts, project conventions, naming patterns;
- durable facts about the user's work, products, clients and goals;
- outcomes worth recalling - what worked, what broke.

Do not store: transient status, secrets, credentials, tokens, private keys, or anything the user
asked you to forget.

### How to save well

1. Write the memory as a self-contained statement, not a chat fragment. "Chose Hono over Express
   for the FriskyDev gateway because of cold-start latency on Workers" survives; "yes like we said"
   does not.
2. Include the reason and the context, not just the conclusion.
3. Use `add_memory` for a single fact and `save-memory` when you want to store a block of content.
   Use `guided-save` when the user is deciding what to keep and wants the interactive picker.
4. Prefer updating an existing memory over creating a near-duplicate. Search first when unsure.

## Organize with spaces and container tags

- `list_spaces` shows the available spaces; `set-active-tag` switches the active space when the
  user is working across several.
- Container tags scope content per project or per user. Keep them consistent - search results are
  far more useful when everything related lives under one tag.
- `memory-graph` and `fetch-graph-data` show how memories relate to each other; use them when the
  user asks what connects to what.

## Forget on request

`forget_memory` removes content. It accepts memory ids from a prior search, or an exact content
string. When the user asks to forget something, search for it first, show what you found, and remove
the specific ids they mean. Deletion is not reversible - confirm the target before removing.

## Profile and identity

`get_profile` returns the stable facts and recent context for the active space. `who_am_i` returns
the account identity and access scope. Use them to answer "what do you know about me" without
guessing.

## Reference

| Tool | Use it for |
|---|---|
| `search_memory` | Semantic recall across memories and documents |
| `add_memory` | Store one durable fact |
| `save-memory` | Store a block of content |
| `guided-save` | Interactive save flow when the user is choosing |
| `get_profile` | Stable facts plus recent context |
| `list_documents` / `get_document` | Browse the document record |
| `list_memories` | List extracted memory entries |
| `list_spaces` / `set-active-tag` | Spaces and container tags |
| `memory-graph` / `fetch-graph-data` | Relationship view |
| `forget_memory` | Remove memories by id or exact content |
| `who_am_i` | Account identity and permissions |

## Guardrails

- Never write a secret, token or credential into a memory. If the user pastes one, save the fact
  without the secret.
- Never print raw stored content that contains personal data beyond what the question needs.
- Storage is persistent and shared across sessions - treat it as durable, and confirm before
  storing something the user only mentioned in passing.
