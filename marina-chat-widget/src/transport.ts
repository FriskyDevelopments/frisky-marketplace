export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  text: string;
}

export interface TransportConfig {
  baseUrl: string;
  agentId: string;
  pollMs: number;
}

export interface TransportCallbacks {
  onMessage: (message: ChatMessage) => void;
  onConnection: (state: 'connecting' | 'realtime' | 'polling' | 'offline') => void;
  onError: (message: string) => void;
}

type JsonRecord = Record<string, unknown>;
type ConnectionState = 'connecting' | 'realtime' | 'polling' | 'offline';

const REALTIME_PROTOCOL = 'ando.realtime.v1';
const EVENTS = ['message.created', 'message.updated'];

function isRecord(value: unknown): value is JsonRecord {
  return typeof value === 'object' && value !== null;
}

function unwrap(value: unknown): unknown {
  if (!isRecord(value)) return value;
  if ('data' in value && value.data !== undefined) return value.data;
  return value;
}

function asMessage(value: unknown, agentId: string): ChatMessage | undefined {
  const outer = unwrap(value);
  if (!isRecord(outer)) return undefined;
  const row = isRecord(outer.message) ? outer.message : outer;
  const id = typeof row.id === 'string' ? row.id : undefined;
  const content = typeof row.content === 'string'
    ? row.content
    : typeof row.markdown_content === 'string' ? row.markdown_content : undefined;
  if (!id || content === undefined) return undefined;

  const authorId = row.authorWorkspaceMembershipId ?? row.author_id ?? row.authorId;
  const role = row.role === 'assistant' || row.role === 'user'
    ? row.role
    : typeof authorId === 'string' && authorId === agentId ? 'assistant' : 'user';
  return { id, role, text: content };
}

function messagesFrom(value: unknown): unknown[] {
  const root = isRecord(value) ? value : {};
  const data = isRecord(root.data) ? root.data : root;
  if (Array.isArray(data.items)) return data.items;
  if (Array.isArray(data.messages)) return data.messages;
  if (Array.isArray(root.items)) return root.items;
  if (Array.isArray(root.messages)) return root.messages;
  return [];
}

function pageInfoFrom(value: unknown): JsonRecord | undefined {
  if (!isRecord(value)) return undefined;
  const data = isRecord(value.data) ? value.data : value;
  if (isRecord(data.page_info)) return data.page_info;
  if (isRecord(value.pageInfo)) return value.pageInfo;
  return undefined;
}

function messageConversationId(value: unknown): string | undefined {
  const row = unwrap(value);
  return isRecord(row) && typeof row.conversation_id === 'string' ? row.conversation_id : undefined;
}

function messageTimestamp(value: unknown): number | undefined {
  const row = unwrap(value);
  if (!isRecord(row)) return undefined;
  const timestamp = row.created_at ?? row.createdAt;
  if (typeof timestamp !== 'string') return undefined;
  const parsed = Date.parse(timestamp);
  return Number.isNaN(parsed) ? undefined : parsed;
}

export class Transport {
  private readonly baseUrl: string;
  private readonly config: TransportConfig;
  private readonly callbacks: TransportCallbacks;
  private conversationId?: string;
  private sessionPromise?: Promise<string>;
  private started = false;
  private stopped = false;
  private state: ConnectionState = 'offline';
  private cursor?: string;
  private socket?: WebSocket;
  private lifeController?: AbortController;
  private pollTimer?: ReturnType<typeof setTimeout>;
  private reconnectTimer?: ReturnType<typeof setTimeout>;
  private reconnectAttempt = 0;
  private realtimeConnecting = false;
  private pollInFlight?: Promise<void>;
  private eventQueue: Promise<void> = Promise.resolve();
  private readonly knownMessages = new Map<string, ChatMessage>();
  private readonly aliases = new Map<string, string>();
  private readonly pendingByText = new Map<string, string[]>();

  constructor(config: TransportConfig, callbacks: TransportCallbacks) {
    this.config = config;
    this.baseUrl = config.baseUrl.replace(/\/$/, '');
    this.callbacks = callbacks;
  }

  async start(): Promise<void> {
    if (this.started && !this.stopped) return;
    this.started = true;
    this.stopped = false;
    this.lifeController = new AbortController();
    this.setState('connecting');
    try {
      await this.ensureSession();
      if (this.stopped) return;
      await this.poll();
      if (this.stopped) return;
      void this.connectRealtime();
    } catch (error) {
      if (this.stopped) return;
      this.reportError(error);
      this.setState('offline');
    }
  }

  async send(text: string, id: string): Promise<void> {
    const optimistic: ChatMessage = { id, role: 'user', text };
    const previous = this.knownMessages.get(id);
    this.remember(optimistic);
    if (!previous || previous.text !== text || previous.role !== 'user') this.callbacks.onMessage(optimistic);
    this.addPendingText(text, id);

    try {
      const conversationId = await this.ensureSession();
      const response = await this.request(
        `/conversations/${encodeURIComponent(conversationId)}/messages`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Idempotency-Key': id },
          body: JSON.stringify({
            markdown_content: text,
            explicit_context_message_ids: [],
            image_urls: [],
            suppressed_link_preview_urls: [],
          }),
        },
      );
      const result = asMessage(response, this.config.agentId);
      if (result) {
        this.aliases.set(result.id, id);
        this.removePendingText(text, id);
        const previous = this.knownMessages.get(id);
        if (previous && previous.text !== result.text) {
          const update = { ...result, id };
          this.remember(update);
          this.callbacks.onMessage(update);
        }
      }
      if (this.started && !this.stopped && (!this.socket || this.socket.readyState !== WebSocket.OPEN)) {
        this.beginPolling();
        if (!this.socket) void this.connectRealtime();
      }
    } catch (error) {
      this.removePendingText(text, id);
      this.reportError(error);
      throw error;
    }
  }

  stop(): void {
    if (this.stopped) return;
    this.stopped = true;
    this.started = false;
    this.lifeController?.abort();
    this.lifeController = undefined;
    if (this.pollTimer) clearTimeout(this.pollTimer);
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.pollTimer = undefined;
    this.reconnectTimer = undefined;
    const socket = this.socket;
    this.socket = undefined;
    if (socket && socket.readyState < WebSocket.CLOSING) socket.close();
    this.setState('offline');
  }

  private async ensureSession(): Promise<string> {
    if (this.conversationId) return this.conversationId;
    if (!this.sessionPromise) {
      this.sessionPromise = this.request('/sessions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agent_id: this.config.agentId }),
      }).then((response) => {
        const body = unwrap(response);
        const id = isRecord(body) && typeof body.conversation_id === 'string'
          ? body.conversation_id
          : isRecord(body) && typeof body.id === 'string' ? body.id : undefined;
        if (!id) throw new Error('The chat proxy did not return a conversation_id');
        this.conversationId = id;
        return id;
      }).catch((error) => {
        this.sessionPromise = undefined;
        throw error;
      });
    }
    return this.sessionPromise;
  }

  private async request(path: string, init: RequestInit = {}): Promise<unknown> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      ...init,
      credentials: 'include',
      signal: this.lifeController?.signal,
    });
    if (!response.ok) {
      let detail = '';
      try {
        const body = await response.json() as unknown;
        if (isRecord(body)) {
          const error = isRecord(body.error) ? body.error : body;
          if (typeof error.message === 'string') detail = `: ${error.message}`;
        }
      } catch { /* Error responses may be empty. */ }
      throw new Error(`Chat request failed (${response.status})${detail}`);
    }
    if (response.status === 204) return undefined;
    return response.json() as Promise<unknown>;
  }

  private setState(state: ConnectionState): void {
    if (this.state === state) return;
    this.state = state;
    this.callbacks.onConnection(state);
  }

  private reportError(error: unknown): void {
    if (error instanceof DOMException && error.name === 'AbortError') return;
    this.callbacks.onError(error instanceof Error ? error.message : String(error));
  }

  private async poll(): Promise<void> {
    if (this.stopped || this.pollInFlight) return this.pollInFlight;
    const operation = (async () => {
      try {
        const conversationId = await this.ensureSession();
        const rows: unknown[] = [];
        const cursors = new Set<string>();
        let before: string | undefined;
        while (!this.stopped) {
          const query = new URLSearchParams({ limit: '100' });
          if (before) query.set('before', before);
          const body = await this.request(
            `/conversations/${encodeURIComponent(conversationId)}/messages?${query.toString()}`,
          );
          if (this.stopped) return;
          rows.push(...messagesFrom(body));
          const pageInfo = pageInfoFrom(body);
          const hasNextPage = pageInfo?.has_next_page === true || pageInfo?.hasNextPage === true;
          if (!hasNextPage) break;
          const nextCursor = pageInfo?.next_cursor ?? pageInfo?.end_cursor ?? pageInfo?.endCursor;
          if (typeof nextCursor !== 'string' || !nextCursor || cursors.has(nextCursor)) {
            throw new Error('The message page did not provide a new next_cursor');
          }
          cursors.add(nextCursor);
          before = nextCursor;
        }
        if (this.stopped) return;
        const ordered = rows.map((raw, index) => ({ raw, index, timestamp: messageTimestamp(raw) }));
        ordered.sort((a, b) => a.timestamp !== undefined && b.timestamp !== undefined
          ? a.timestamp - b.timestamp || a.index - b.index
          : a.index - b.index);
        for (const { raw } of ordered) {
          if (this.stopped || messageConversationId(raw) !== conversationId) continue;
          const message = asMessage(raw, this.config.agentId);
          if (message) this.publish(message);
        }
        if (!this.socket || this.socket.readyState !== WebSocket.OPEN) this.setState('polling');
      } catch (error) {
        if (this.stopped) return;
        this.reportError(error);
        if (!this.socket || this.socket.readyState !== WebSocket.OPEN) this.setState('offline');
      } finally {
        this.pollInFlight = undefined;
        if (this.started && !this.stopped && (!this.socket || this.socket.readyState !== WebSocket.OPEN)) {
          this.schedulePoll();
        }
      }
    })();
    this.pollInFlight = operation;
    return operation;
  }

  private beginPolling(): void {
    if (this.stopped || !this.started || (this.socket && this.socket.readyState === WebSocket.OPEN)) return;
    if (this.pollTimer) clearTimeout(this.pollTimer);
    void this.poll();
  }

  private schedulePoll(): void {
    if (this.pollTimer) clearTimeout(this.pollTimer);
    this.pollTimer = setTimeout(() => {
      this.pollTimer = undefined;
      void this.poll();
    }, Math.max(250, this.config.pollMs));
  }

  private async connectRealtime(): Promise<void> {
    if (this.stopped || !this.started || this.realtimeConnecting || (this.socket && this.socket.readyState < WebSocket.CLOSING)) return;
    this.realtimeConnecting = true;
    this.setState('connecting');
    try {
      await this.ensureSession();
      if (this.stopped) {
        this.realtimeConnecting = false;
        return;
      }
    } catch (error) {
      if (!this.stopped) {
        this.reportError(error);
        this.setState('offline');
        this.beginPolling();
        this.scheduleReconnect();
      }
      this.realtimeConnecting = false;
      return;
    }

    try {
      const body = await this.request('/realtime/connections', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          subscriptions: [{ target: 'self', delivery: 'messages', events: EVENTS }],
          resume_from: this.cursor ? { cursor: this.cursor } : undefined,
        }),
      });
      if (this.stopped) return;
      const ticket = unwrap(body);
      if (!isRecord(ticket) || typeof ticket.url !== 'string' || typeof ticket.resume_cursor !== 'string') {
        throw new Error('The chat proxy returned an invalid realtime connection ticket');
      }
      this.cursor = ticket.resume_cursor;
      const socket = new WebSocket(ticket.url, REALTIME_PROTOCOL);
      this.socket = socket;
      socket.onopen = () => {
        if (this.stopped || this.socket !== socket) return;
        this.reconnectAttempt = 0;
        if (this.pollTimer) clearTimeout(this.pollTimer);
        this.pollTimer = undefined;
        this.setState('realtime');
      };
      socket.onmessage = (event: MessageEvent<string>) => {
        if (this.stopped || this.socket !== socket) return;
        this.receiveFrame(socket, event.data);
      };
      socket.onerror = () => {
        if (!this.stopped) {
          this.setState('polling');
          this.beginPolling();
        }
      };
      socket.onclose = () => {
        if (this.socket !== socket) return;
        this.socket = undefined;
        if (this.stopped) return;
        this.setState('polling');
        this.beginPolling();
        this.scheduleReconnect();
      };
    } catch (error) {
      if (this.stopped) return;
      this.setState('polling');
      this.beginPolling();
      this.scheduleReconnect();
    } finally {
      this.realtimeConnecting = false;
    }
  }

  private receiveFrame(socket: WebSocket, raw: unknown): void {
    let frame: unknown;
    try {
      frame = typeof raw === 'string' ? JSON.parse(raw) as unknown : undefined;
    } catch {
      this.reportError(new Error('Realtime server sent invalid JSON'));
      return;
    }
    if (!isRecord(frame) || typeof frame.type !== 'string') return;
    if (frame.type === 'acknowledged' && typeof frame.resume_cursor === 'string') {
      this.cursor = frame.resume_cursor;
      return;
    }
    if (frame.type === 'disconnect') {
      if (typeof frame.resume_cursor === 'string') this.cursor = frame.resume_cursor;
      if (socket.readyState < WebSocket.CLOSING) socket.close();
      return;
    }
    if (frame.type !== 'event' || typeof frame.envelope_id !== 'string') return;
    this.eventQueue = this.eventQueue.then(async () => {
      if (this.stopped) return;
      try {
        const event = isRecord(frame.payload) ? frame.payload : undefined;
        const related = event && isRecord(event.related) ? event.related : undefined;
        const data = event && isRecord(event.data) ? event.data : undefined;
        const object = data && isRecord(data.object) ? data.object : undefined;
        const messageId = typeof object?.id === 'string'
          ? object.id
          : typeof related?.message_id === 'string' ? related.message_id : undefined;
        const isMessageEvent = event?.type === 'message.created' || event?.type === 'message.updated';
        const conversationId = this.conversationId;
        const relatedConversationId = typeof related?.conversation_id === 'string'
          ? related.conversation_id
          : typeof object?.conversation_id === 'string' ? object.conversation_id : undefined;
        if (isMessageEvent && messageId && conversationId &&
            (!relatedConversationId || relatedConversationId === conversationId)) {
          const response = await this.request(`/conversation-messages/${encodeURIComponent(messageId)}`);
          if (this.stopped) return;
          const message = asMessage(response, this.config.agentId);
          if (message && messageConversationId(response) === conversationId) this.publish(message);
        }
        if (this.stopped) return;
        if (socket.readyState === WebSocket.OPEN) socket.send(JSON.stringify({ envelope_id: frame.envelope_id }));
      } catch (error) {
        if (this.stopped) return;
        this.reportError(error);
        if (socket.readyState === WebSocket.OPEN) {
          socket.send(JSON.stringify({ envelope_id: frame.envelope_id, error: { code: 'handler_failed' } }));
        }
      }
    }).catch((error: unknown) => this.reportError(error));
  }

  private publish(message: ChatMessage): void {
    const displayId = this.aliases.get(message.id) ?? this.pendingMatch(message);
    if (displayId && displayId !== message.id) this.aliases.set(message.id, displayId);
    const normalized = displayId ? { ...message, id: displayId } : message;
    const previous = this.knownMessages.get(normalized.id);
    if (previous?.text === normalized.text && previous.role === normalized.role) return;
    this.remember(normalized);
    this.callbacks.onMessage(normalized);
  }

  private remember(message: ChatMessage): void {
    this.knownMessages.set(message.id, message);
  }

  private pendingMatch(message: ChatMessage): string | undefined {
    if (message.role !== 'user') return undefined;
    const pending = this.pendingByText.get(message.text);
    const id = pending?.[0];
    if (id) this.removePendingText(message.text, id);
    return id;
  }

  private addPendingText(text: string, id: string): void {
    const ids = this.pendingByText.get(text) ?? [];
    if (!ids.includes(id)) ids.push(id);
    this.pendingByText.set(text, ids);
  }

  private removePendingText(text: string, id: string): void {
    const ids = this.pendingByText.get(text);
    if (!ids) return;
    const remaining = ids.filter((item) => item !== id);
    if (remaining.length) this.pendingByText.set(text, remaining);
    else this.pendingByText.delete(text);
  }

  private scheduleReconnect(): void {
    if (this.stopped || !this.started || this.reconnectTimer) return;
    const delay = Math.min(30_000, 500 * 2 ** Math.min(this.reconnectAttempt, 6));
    this.reconnectAttempt += 1;
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = undefined;
      void this.connectRealtime();
    }, delay);
  }
}
