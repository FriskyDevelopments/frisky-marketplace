# Marina Chat widget

A self-contained React + TypeScript chat bubble built with Vite and
`@assistant-ui/react`'s `useExternalStoreRuntime`. It mounts into an open Shadow
DOM, with all CSS embedded in the JavaScript. React and assistant-ui are bundled;
the host does not need either. No API key is accepted or shipped to the browser.

## Develop and build

Requires Node 22.12+ (or 20.19+) and pnpm 10.

```sh
cd marina-chat-widget
pnpm install --frozen-lockfile
pnpm test
pnpm build
pnpm dev
```

The build emits `dist/marina-chat.iife.js` for script embeds and
`dist/marina-chat.js` for ES imports. A build-time size gate requires the
**complete standalone IIFE, including styles and dependencies**, to stay below
150 KiB gzip. The initial build is approximately 123 KiB gzip. `dist/` is not
committed. This project includes no deployment configuration.

The development playground simulates REST replies locally and deliberately uses
polling. It does not contact Ando. Select a brand with the links or `?theme=`.
The demo's fetch shim is **not included** in the production library.
After building, open `/?build=1` to exercise the actual IIFE rather than the
development modules; combine it with `&theme=codepup` or
`&theme=nebu`.

## Script embeds by brand

Serve the built IIFE from your own static asset origin; the URLs below are
placeholders, not deployed assets. Supply an allowed agent ID and a **server-side
proxy URL**, not Ando's authenticated API URL.

### marina · Marina

Bugambilia flower icon, purple `#9B3FB0`, gold heart `#C9A24B`.

```html
<script defer src="/assets/marina-chat.iife.js"
  data-agent-id="YOUR_MARINA_AGENT_ID"
  data-base-url="/api/chat"
  data-theme="marina"
  data-title="Marina"
  data-greeting="Hola, I’m Marina. What’s on your mind?"
  data-position="right"></script>
```

### codepup · Codepup

Hot pink `#ff006b`, uppercase assistant voice and interface copy. Visitor
messages remain unchanged; uppercase is a presentation choice, not a mutation
of the transport payload.

```html
<script defer src="/assets/marina-chat.iife.js"
  data-agent-id="YOUR_CODEPUP_AGENT_ID"
  data-base-url="/api/chat"
  data-theme="codepup"
  data-title="CODEPUP"
  data-greeting="HEY, I’M CODEPUP. WHAT ARE WE BUILDING?"
  data-position="right"></script>
```

### nebu · Nebu / Ashy

Ash neutrals, soft violet, restrained cyan status text, and yellow only on the
main send CTA. No yellow loading dot or gold heart in this preset.

```html
<script defer src="/assets/marina-chat.iife.js"
  data-agent-id="YOUR_NEBU_AGENT_ID"
  data-base-url="/api/chat"
  data-theme="nebu"
  data-title="Ashy · Nebu"
  data-greeting="A little clarity, a little space. How can I help?"
  data-position="left"></script>
```

These are the only three presets. **Fenrir is not a preset**; unknown theme names
fall back to marina.

## Configuration

Set `window.MarinaChatConfig` **before** loading the script, or supply data
attributes. Attributes take priority over global configuration; explicit values
take priority over theme defaults.

```html
<script>
  window.MarinaChatConfig = {
    agentId: 'YOUR_AGENT_ID',
    baseUrl: '/api/chat',
    theme: 'marina',
    title: 'Marina',
    accent: '#9B3FB0',
    icon: 'bugambilia',
    greeting: 'Let’s talk.',
    position: 'right',
    streamCps: 60,
    pollMs: 2500
  };
</script>
<script defer src="/assets/marina-chat.iife.js"></script>
```

| Attribute | Global key | Default / values |
| --- | --- | --- |
| `data-agent-id` | `agentId` | Required; no implicit agent |
| `data-base-url` | `baseUrl` | `/api/marina-chat`; HTTP(S) proxy prefix |
| `data-theme` | `theme` | `marina`, `codepup`, `nebu` |
| `data-title` | `title` | Brand default |
| `data-accent` | `accent` | Brand default; hex color |
| `data-icon` | `icon` | `bugambilia`, `pup`, `star`, text, or HTTP(S) image URL |
| `data-greeting` | `greeting` | Brand default |
| `data-position` | `position` | `right` or `left` |
| `data-stream-cps` | `streamCps` | 60; clamped to 1–1000 |
| `data-poll-ms` | `pollMs` | 2500; clamped to 500–60000 |

All message text is rendered as plain text, never injected HTML. Image URLs are
loaded with `referrerPolicy="no-referrer"`. Allow the asset/image origins,
proxy HTTP endpoint, ticket WebSocket origin, and the widget's inline Shadow DOM
styles in your site's CSP. Custom fonts are not required.

For manual lifecycle control, use the ES build (no auto-mount):

```js
import { mount } from '/assets/marina-chat.js';
const chat = mount({ agentId: 'YOUR_AGENT_ID', baseUrl: '/api/chat' });
// When your host route is destroyed:
chat.unmount();
```

The IIFE auto-mounts once per script tag and also exposes `MarinaChat.mount()`.
Mounting into an optional container attaches a Shadow DOM to that container.
Configuration is read at mount time; unmount/remount to change it.

## Proxy and Ando transport contract

Ando is a **server-side API-key integration**, not a public unauthenticated chat
endpoint. Implement the following contract in your own proxy. The widget does
not include a backend or assume a direct browser-to-Ando agent route.

1. `POST {baseUrl}/sessions` with `{ "agent_id": "..." }` returns
   `{ "conversation_id": "..." }`. This is a **widget-specific proxy endpoint**,
   not an Ando endpoint. Establish a visitor-scoped session (for example an
   HttpOnly cookie), create/select that visitor's conversation, add the selected
   agent, and return only an authorized conversation ID.
2. Forward `GET /conversations/{conversationId}/messages` using Ando's
   `data.items` / `data.page_info` envelope and cursor pagination. Items must have
   `id`, `conversation_id`, `markdown_content`, and either a normalized `role`
   (`user`/`assistant`) or Ando author identity fields. Preserve timestamps for
   ordering; the proxy may normalize agent author records to `role: assistant`.
3. Forward `POST /conversations/{conversationId}/messages` with
   `{ "markdown_content": "...", "explicit_context_message_ids": [],
   "image_urls": [], "suppressed_link_preview_urls": [] }` and the widget's
   `Idempotency-Key` header. Return the created message in `{ "data": message }`.
   Retrying a failed send reuses that key. Ando derives the author from your
   server-side credential; the widget sends no author ID.
4. Forward `POST /realtime/connections` with `subscriptions` for `target: self`,
   `delivery: messages`, and `message.created` / `message.updated`. On reconnect,
   the widget supplies `resume_from: { cursor }`. Return Ando's temporary `url`,
   `protocol`, and `resume_cursor` (a `data` wrapper is also supported). **Scope
   the upstream identity/subscription to this visitor**; filtering in the widget
   is not an authorization boundary. Do not expose a workspace-wide ticket.
5. Forward `GET /conversation-messages/{messageId}` for bounded event references.

The proxy adds the server-side `x-api-key`. Enforce agent allowlists,
conversation/message ownership, body limits, rate limits, origin/CSRF controls,
and suitable CORS. Fetch uses `credentials: include`; cross-origin proxies need
an explicit allowed origin, credentials-enabled CORS, and permitted
`Content-Type` / `Idempotency-Key` headers. Never return a key in session data or
in a WebSocket URL. The only browser-visible credential is a temporary realtime
ticket. Do not cache ticket/session responses publicly.

The WebSocket uses **`ando.realtime.v1`**. Event processing is serialized and each
event is acknowledged in arrival order with `{ "envelope_id": "..." }`, including
duplicates and unrelated events. Handler failures use an error acknowledgment.
Only server-confirmed `acknowledged`/`disconnect` cursors advance resume state;
event cursors do not. Every close requests a fresh ticket with bounded exponential
backoff. Polling runs while realtime is unavailable and stops on connection.
Message IDs deduplicate REST, realtime, and optimistic echoes; edits with changed
text update the existing message. Unmount aborts requests and clears timers/socket.
Sessions and cursors are in-memory only; reload starts a new proxy session request.

## Interaction and accessibility

- Dark floating bubble; 360 × 520 panel, `#0d0d11` background and `#e9e9ee` text.
  Smaller screens constrain panel dimensions to fit the viewport.
- Assistant text reveals in whole words at approximately 60 characters/second,
  accelerated for a maximum four-second reveal. Click the message to skip.
- `prefers-reduced-motion` disables animation and reveals complete text instantly.
- Icon states: idle sway, thinking spin/breathe with three dots, ready settle.
- Connection dot distinguishes connecting, realtime, polling, and offline.
- Enter sends; Shift+Enter adds a newline; IME composition does not submit.
  Escape closes and restores launcher focus. The nonmodal panel does not trap
  focus or block the host page.
- Full assistant messages have polite, atomic live announcements; animation
  frames are hidden from screen readers. Errors and thinking have accessible
  status announcements.
- Failed sends offer Retry. A 60-second reply timeout releases the composer;
  late replies still appear.

## Verification and references

Unit tests cover configuration, preset restrictions, whole-word reveal/cap,
reduced motion, runtime submission, keyboard/focus behavior, retry/session
initialization, dedupe/updates, polling, ordered acknowledgments, resume cursors,
and teardown. Browser verification uses the local simulated playground; a live
Ando/proxy integration still requires your server and credentials.

- [assistant-ui external store runtime](https://www.assistant-ui.com/docs/runtimes/custom/external-store)
- [Ando public API overview](https://docs.ando.so/api-reference/overview)
- [Ando realtime contract](https://docs.ando.so/developers/realtime)
- [Ando current OpenAPI schema](https://api.ando.so/openapi.json)
