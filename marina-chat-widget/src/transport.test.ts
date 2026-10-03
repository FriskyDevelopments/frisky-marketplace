import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { Transport, type ChatMessage } from './transport';

class FakeWebSocket {
  static instances: FakeWebSocket[] = [];
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;
  readyState = FakeWebSocket.CONNECTING;
  onopen: (() => void) | null = null;
  onmessage: ((event: MessageEvent<string>) => void) | null = null;
  onerror: (() => void) | null = null;
  onclose: (() => void) | null = null;
  sent: string[] = [];
  constructor(readonly url: string, readonly protocol: string) { FakeWebSocket.instances.push(this); }
  open() { this.readyState = FakeWebSocket.OPEN; this.onopen?.(); }
  message(data: unknown) { this.onmessage?.({ data: JSON.stringify(data) } as MessageEvent<string>); }
  send(data: string) { this.sent.push(data); }
  close() { this.readyState = FakeWebSocket.CLOSED; this.onclose?.(); }
}

const config = { baseUrl: 'https://proxy.test/api', agentId: 'agent-1', pollMs: 1000 };
let messages: ChatMessage[];
let states: string[];
let errors: string[];
let transport: Transport;
let fetchMock: ReturnType<typeof vi.fn>;

function json(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), { status, headers: { 'Content-Type': 'application/json' } });
}

function makeTransport() {
  messages = [];
  states = [];
  errors = [];
  transport = new Transport(config, {
    onMessage: (message) => messages.push(message),
    onConnection: (state) => states.push(state),
    onError: (message) => errors.push(message),
  });
  return transport;
}

function realtimeTicket() {
  return { url: 'wss://proxy.test/realtime/ticket', resume_cursor: 'cursor-0' };
}

async function flushPromises() {
  for (let i = 0; i < 10; i += 1) await Promise.resolve();
}

beforeEach(() => {
  vi.useFakeTimers();
  FakeWebSocket.instances = [];
  vi.stubGlobal('WebSocket', FakeWebSocket);
  fetchMock = vi.fn();
  vi.stubGlobal('fetch', fetchMock);
});

afterEach(() => {
  transport?.stop();
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe('Transport', () => {
  it('deduplicates a realtime echo arriving before the send response', async () => {
    const serverMessage = { id: 'server-id', conversation_id: 'conversation-1', role: 'user', markdown_content: 'hello' };
    let resolveSend!: (response: Response) => void;
    fetchMock
      .mockResolvedValueOnce(json({ conversation_id: 'conversation-1' }))
      .mockResolvedValueOnce(json({ data: { items: [] } }))
      .mockResolvedValueOnce(json(realtimeTicket()))
      .mockReturnValueOnce(new Promise<Response>(resolve => { resolveSend = resolve; }))
      .mockResolvedValueOnce(json({ data: serverMessage }));
    makeTransport();
    await transport.start();
    await vi.waitFor(() => expect(FakeWebSocket.instances).toHaveLength(1));
    const socket = FakeWebSocket.instances[0];
    socket.open();
    const send = transport.send('hello', 'optimistic-id');
    await vi.waitFor(() => expect(fetchMock.mock.calls).toHaveLength(4));
    socket.message({ type: 'event', envelope_id: 'echo', payload: {
      type: 'message.created', related: { message_id: 'server-id', conversation_id: 'conversation-1' },
    } });
    await vi.waitFor(() => expect(socket.sent).toHaveLength(1));
    expect(messages).toEqual([{ id: 'optimistic-id', role: 'user', text: 'hello' }]);
    resolveSend(json({ data: serverMessage }));
    await send;
    expect(messages).toHaveLength(1);
  });
  it('creates a proxied session and opens a subscribed realtime socket', async () => {
    fetchMock
      .mockResolvedValueOnce(json({ conversation_id: 'conversation-1' }))
      .mockResolvedValueOnce(json({ data: { items: [] } }))
      .mockResolvedValueOnce(json(realtimeTicket()));
    makeTransport();

    await transport.start();
    await vi.waitFor(() => expect(FakeWebSocket.instances).toHaveLength(1));
    const socket = FakeWebSocket.instances[0];
    expect(socket.protocol).toBe('ando.realtime.v1');
    expect(fetchMock.mock.calls[0][0]).toBe('https://proxy.test/api/sessions');
    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({ agent_id: 'agent-1' });
    expect(fetchMock.mock.calls.every(([, init]) => init.credentials === 'include')).toBe(true);
    const ticketRequest = fetchMock.mock.calls[2];
    expect(ticketRequest[0]).toBe('https://proxy.test/api/realtime/connections');
    expect(JSON.parse(ticketRequest[1].body)).toEqual({
      subscriptions: [{ target: 'self', delivery: 'messages', events: ['message.created', 'message.updated'] }],
    });
    socket.open();
    expect(states.at(-1)).toBe('realtime');
  });

  it('fetches message references and acknowledges every event in arrival order', async () => {
    fetchMock
      .mockResolvedValueOnce(json({ conversation_id: 'conversation-1' }))
      .mockResolvedValueOnce(json({ data: { items: [] } }))
      .mockResolvedValueOnce(json(realtimeTicket()))
      .mockResolvedValueOnce(json({ data: {
        id: 'm-1', conversation_id: 'conversation-1', content: 'hello', authorWorkspaceMembershipId: 'agent-1',
      } }));
    makeTransport();
    await transport.start();
    await vi.waitFor(() => expect(FakeWebSocket.instances).toHaveLength(1));
    const socket = FakeWebSocket.instances[0];
    socket.open();
    socket.message({ type: 'event', envelope_id: 'e-1', payload: {
      id: 'p-1', type: 'message.created', related: { message_id: 'm-1', conversation_id: 'conversation-1' },
      data: { object: { id: 'm-1', conversation_id: 'conversation-1' } },
    } });
    await vi.waitFor(() => expect(socket.sent).toHaveLength(1));
    expect(fetchMock.mock.calls[3][0]).toBe('https://proxy.test/api/conversation-messages/m-1');
    expect(messages).toEqual([{ id: 'm-1', role: 'assistant', text: 'hello' }]);
    expect(JSON.parse(socket.sent[0])).toEqual({ envelope_id: 'e-1' });
  });

  it('paginates polling with before cursors and emits messages oldest first', async () => {
    fetchMock
      .mockResolvedValueOnce(json({ conversation_id: 'conversation-1' }))
      .mockResolvedValueOnce(json({ data: {
        items: [
          { id: 'new', conversation_id: 'conversation-1', markdown_content: 'new', role: 'assistant', created_at: '2026-01-03T00:00:00Z' },
          { id: 'middle', conversation_id: 'conversation-1', markdown_content: 'middle', role: 'assistant', created_at: '2026-01-02T00:00:00Z' },
        ],
        page_info: { has_next_page: true, next_cursor: 'older-page' },
      } }))
      .mockResolvedValueOnce(json({ data: {
        items: [{ id: 'old', conversation_id: 'conversation-1', markdown_content: 'old', role: 'user', created_at: '2026-01-01T00:00:00Z' }],
        page_info: { has_next_page: false, next_cursor: null },
      } }))
      .mockResolvedValueOnce(json(realtimeTicket()));
    makeTransport();

    await transport.start();

    expect(fetchMock.mock.calls[1][0]).toBe('https://proxy.test/api/conversations/conversation-1/messages?limit=100');
    expect(fetchMock.mock.calls[2][0]).toBe('https://proxy.test/api/conversations/conversation-1/messages?limit=100&before=older-page');
    expect(messages.map(({ id }) => id)).toEqual(['old', 'middle', 'new']);
  });

  it('acknowledges unrelated realtime events without fetching or publishing them', async () => {
    fetchMock
      .mockResolvedValueOnce(json({ conversation_id: 'conversation-1' }))
      .mockResolvedValueOnce(json({ items: [] }))
      .mockResolvedValueOnce(json(realtimeTicket()))
      .mockResolvedValueOnce(json({ id: 'foreign', conversation_id: 'conversation-2', content: 'private' }));
    makeTransport();
    await transport.start();
    await vi.waitFor(() => expect(FakeWebSocket.instances).toHaveLength(1));
    const socket = FakeWebSocket.instances[0];
    socket.open();

    socket.message({ type: 'event', envelope_id: 'unrelated', payload: {
      id: 'p-foreign', type: 'message.created',
      related: { message_id: 'foreign', conversation_id: 'conversation-2' },
      data: { object: { id: 'foreign', conversation_id: 'conversation-2' } },
    } });
    socket.message({ type: 'event', envelope_id: 'wrong-message', payload: {
      id: 'p-wrong', type: 'message.created',
      related: { message_id: 'foreign', conversation_id: 'conversation-1' },
      data: { object: { id: 'foreign', conversation_id: 'conversation-1' } },
    } });

    await vi.waitFor(() => expect(socket.sent).toHaveLength(2));
    expect(fetchMock.mock.calls.filter(([url]) => String(url).includes('/conversation-messages/'))).toHaveLength(1);
    expect(messages).toEqual([]);
    expect(socket.sent.map((item) => JSON.parse(item).envelope_id)).toEqual(['unrelated', 'wrong-message']);
  });

  it('does not create a socket when stopped while fetching a realtime ticket', async () => {
    let resolveTicket!: (response: Response) => void;
    const ticketResponse = new Promise<Response>((resolve) => { resolveTicket = resolve; });
    fetchMock
      .mockResolvedValueOnce(json({ conversation_id: 'conversation-1' }))
      .mockResolvedValueOnce(json({ items: [] }))
      .mockReturnValueOnce(ticketResponse);
    makeTransport();

    await transport.start();
    await vi.waitFor(() => expect(fetchMock.mock.calls.some(([url]) => String(url).endsWith('/realtime/connections'))).toBe(true));
    transport.stop();
    resolveTicket(json(realtimeTicket()));
    await flushPromises();

    expect(FakeWebSocket.instances).toHaveLength(0);
  });

  it('skips queued event fetches and acknowledgements after stop', async () => {
    let resolveMessage!: (response: Response) => void;
    const messageResponse = new Promise<Response>((resolve) => { resolveMessage = resolve; });
    fetchMock
      .mockResolvedValueOnce(json({ conversation_id: 'conversation-1' }))
      .mockResolvedValueOnce(json({ items: [] }))
      .mockResolvedValueOnce(json(realtimeTicket()))
      .mockReturnValueOnce(messageResponse);
    makeTransport();
    await transport.start();
    await vi.waitFor(() => expect(FakeWebSocket.instances).toHaveLength(1));
    const socket = FakeWebSocket.instances[0];
    socket.open();
    const event = (envelopeId: string, messageId: string) => ({
      type: 'event', envelope_id: envelopeId, payload: {
        type: 'message.created',
        related: { message_id: messageId, conversation_id: 'conversation-1' },
      },
    });
    socket.message(event('e-1', 'm-1'));
    await vi.waitFor(() => expect(fetchMock.mock.calls.filter(([url]) => String(url).includes('/conversation-messages/'))).toHaveLength(1));
    socket.message(event('e-2', 'm-2'));
    transport.stop();
    resolveMessage(json({ id: 'm-1', conversation_id: 'conversation-1', content: 'late' }));
    await flushPromises();

    expect(fetchMock.mock.calls.filter(([url]) => String(url).includes('/conversation-messages/'))).toHaveLength(1);
    expect(socket.sent).toEqual([]);
    expect(messages).toEqual([]);
  });

  it('resumes a fresh ticket from the last server-acknowledged cursor', async () => {
    fetchMock
      .mockResolvedValueOnce(json({ conversation_id: 'conversation-1' }))
      .mockResolvedValueOnce(json({ items: [] }))
      .mockResolvedValueOnce(json(realtimeTicket()))
      .mockResolvedValueOnce(json({ items: [] }))
      .mockResolvedValueOnce(json({ ...realtimeTicket(), resume_cursor: 'cursor-1' }))
      .mockResolvedValue(json({ items: [] }));
    makeTransport();
    await transport.start();
    await vi.waitFor(() => expect(FakeWebSocket.instances).toHaveLength(1));
    const socket = FakeWebSocket.instances[0];
    socket.open();
    socket.message({ type: 'acknowledged', envelope_id: 'e-1', resume_cursor: 'cursor-1' });
    socket.close();
    await vi.advanceTimersByTimeAsync(500);
    await vi.waitFor(() => expect(fetchMock.mock.calls.filter(([url]) => url.endsWith('/realtime/connections'))).toHaveLength(2));
    const ticketCalls = fetchMock.mock.calls.filter(([url]) => url.endsWith('/realtime/connections'));
    expect(JSON.parse(ticketCalls[1][1].body)).toEqual({
      subscriptions: [{ target: 'self', delivery: 'messages', events: ['message.created', 'message.updated'] }],
      resume_from: { cursor: 'cursor-1' },
    });
  });

  it('deduplicates polling snapshots, but publishes edits to existing message IDs', async () => {
    fetchMock
      .mockResolvedValueOnce(json({ conversation_id: 'conversation-1' }))
      .mockResolvedValueOnce(json({ items: [{ id: 'm-1', conversation_id: 'conversation-1', content: 'first', role: 'assistant' }] }))
      .mockResolvedValueOnce(json(realtimeTicket()))
      .mockResolvedValueOnce(json({ items: [{ id: 'm-1', conversation_id: 'conversation-1', content: 'first', role: 'assistant' }] }));
    makeTransport();
    await transport.start();
    expect(messages).toEqual([{ id: 'm-1', role: 'assistant', text: 'first' }]);
    await vi.advanceTimersByTimeAsync(1000);
    expect(messages).toHaveLength(1);
    const socket = FakeWebSocket.instances[0];
    socket.open();
    socket.message({ type: 'event', envelope_id: 'e-2', payload: {
      id: 'p-2', type: 'message.updated', related: { message_id: 'm-1', conversation_id: 'conversation-1' },
      data: { object: { id: 'm-1', conversation_id: 'conversation-1' } },
    } });
    fetchMock.mockResolvedValueOnce(json({ id: 'm-1', conversation_id: 'conversation-1', content: 'edited', role: 'assistant' }));
    await vi.waitFor(() => expect(messages.at(-1)?.text).toBe('edited'));
  });

  it('uses the idempotency key and correlates the optimistic user message', async () => {
    fetchMock
      .mockResolvedValueOnce(json({ conversation_id: 'conversation-1' }))
      .mockResolvedValueOnce(json({ success: true, data: { id: 'server-m1', content: 'hi', authorWorkspaceMembershipId: 'visitor-1' } }));
    makeTransport();
    await transport.send('hi', 'client-m1');
    const [url, init] = fetchMock.mock.calls[1];
    expect(url).toBe('https://proxy.test/api/conversations/conversation-1/messages');
    expect(init.headers['Idempotency-Key']).toBe('client-m1');
    expect(init.credentials).toBe('include');
    expect(JSON.parse(init.body)).toEqual({
      markdown_content: 'hi',
      explicit_context_message_ids: [],
      image_urls: [],
      suppressed_link_preview_urls: [],
    });
    expect(messages).toEqual([{ id: 'client-m1', role: 'user', text: 'hi' }]);
  });

  it('retries session initialization after a failed session request', async () => {
    fetchMock
      .mockResolvedValueOnce(json({ message: 'unavailable' }, 503))
      .mockResolvedValueOnce(json({ conversation_id: 'conversation-2' }))
      .mockResolvedValueOnce(json({ success: true, data: { id: 'm-2', content: 'retry', author_id: 'visitor-1' } }));
    makeTransport();
    await expect(transport.send('retry', 'send-2')).rejects.toThrow('503');
    await transport.send('retry', 'send-2');
    expect(fetchMock.mock.calls.filter(([url]) => url.endsWith('/sessions'))).toHaveLength(2);
    expect(fetchMock.mock.calls.at(-1)?.[0]).toContain('/conversations/conversation-2/messages');
  });

  it('can recover a failed startup session when the visitor sends again', async () => {
    fetchMock
      .mockResolvedValueOnce(json({ message: 'temporarily unavailable' }, 503))
      .mockResolvedValueOnce(json({ conversation_id: 'conversation-3' }))
      .mockResolvedValueOnce(json({ success: true, data: { id: 'm-3', content: 'hello', author_id: 'visitor-1' } }))
      .mockResolvedValueOnce(json(realtimeTicket()));
    makeTransport();

    await transport.start();
    await transport.send('hello', 'send-3');
    expect(fetchMock.mock.calls.filter(([url]) => url.endsWith('/sessions'))).toHaveLength(2);
    expect(fetchMock.mock.calls.some(([url]) => url.endsWith('/realtime/connections'))).toBe(true);
    expect(errors).toContain('Chat request failed (503): temporarily unavailable');
    expect(messages).toEqual([{ id: 'send-3', role: 'user', text: 'hello' }]);
  });

  it('silently falls back to healthy polling and stops timers and the active socket', async () => {
    fetchMock
      .mockResolvedValueOnce(json({ conversation_id: 'conversation-1' }))
      .mockResolvedValueOnce(json({ items: [] }))
      .mockResolvedValueOnce(json({ message: 'realtime down' }, 503));
    makeTransport();
    await transport.start();
    await vi.waitFor(() => expect(states).toContain('polling'));
    await vi.waitFor(() => expect(fetchMock.mock.calls.filter(([url]) => url.endsWith('/realtime/connections'))).toHaveLength(1));
    expect(errors).toEqual([]);
    await vi.advanceTimersByTimeAsync(500);
    expect(fetchMock.mock.calls.filter(([url]) => url.endsWith('/realtime/connections'))).toHaveLength(2);
    transport.stop();
    const callCount = fetchMock.mock.calls.length;
    await vi.advanceTimersByTimeAsync(5000);
    expect(fetchMock.mock.calls).toHaveLength(callCount);
    expect(states.at(-1)).toBe('offline');
  });

  it('keeps polling REST failures visible when realtime is unavailable', async () => {
    fetchMock
      .mockResolvedValueOnce(json({ conversation_id: 'conversation-1' }))
      .mockResolvedValueOnce(json({ message: 'poll unavailable' }, 503))
      .mockResolvedValueOnce(json({ message: 'realtime down' }, 503));
    makeTransport();

    await transport.start();
    await vi.waitFor(() => expect(errors).toContain('Chat request failed (503): poll unavailable'));
    expect(states).toContain('offline');
  });

  it('does not surface WebSocket errors when the UI reports connection state', async () => {
    fetchMock
      .mockResolvedValueOnce(json({ conversation_id: 'conversation-1' }))
      .mockResolvedValueOnce(json({ items: [] }))
      .mockResolvedValueOnce(json(realtimeTicket()));
    makeTransport();

    await transport.start();
    await vi.waitFor(() => expect(FakeWebSocket.instances).toHaveLength(1));
    FakeWebSocket.instances[0].onerror?.();
    expect(errors).toEqual([]);
  });
});
