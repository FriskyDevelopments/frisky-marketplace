import { useEffect, useRef, useState, type CSSProperties, type FormEvent } from 'react';
import { AssistantRuntimeProvider, useExternalStoreRuntime, type AppendMessage } from '@assistant-ui/react';
import { themes, type Config } from './config';
import { Reveal } from './reveal';
import { Transport, type ChatMessage } from './transport';

export function BrandIcon({ icon, state = 'idle' }: { icon: string; state?: string }) {
  const remote = /^https?:\/\//i.test(icon);
  return <span className={`brand-icon ${state}`} aria-hidden="true">
    {remote ? <img src={icon} alt="" referrerPolicy="no-referrer" /> : icon === 'bugambilia' ?
      <svg viewBox="0 0 48 48" fill="none"><path d="M24 25C3 31 5 9 17 9c7 0 9 10 7 16Z" fill="var(--accent)"/><path d="M24 25c-3-23 20-25 20-12 0 8-12 13-20 12Z" fill="var(--accent)" opacity=".8"/><path d="M24 25c24 0 18 24 6 20-7-2-7-14-6-20Z" fill="var(--accent)" opacity=".6"/><path d="M24 22c-5-5-10 2 0 8 10-6 5-13 0-8Z" fill="var(--heart)"/></svg> :
      <span className="symbol">{icon === 'pup' ? '⌁' : icon === 'star' ? '✧' : icon}</span>}
  </span>;
}

export function Widget({ config }: { config: Config }) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([{ id: 'greeting', role: 'assistant', text: config.greeting }]);
  const [running, setRunning] = useState(false);
  const [connection, setConnection] = useState('connecting');
  const [error, setError] = useState('');
  const [draft, setDraft] = useState('');
  const [failed, setFailed] = useState<{ text: string; id: string }>();
  const transport = useRef<Transport | null>(null);
  const launcher = useRef<HTMLButtonElement>(null);
  const input = useRef<HTMLTextAreaElement>(null);
  const log = useRef<HTMLDivElement>(null);
  const pending = useRef(false);
  const timeout = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const clearPending = () => {
    clearTimeout(timeout.current);
    pending.current = false;
    setRunning(false);
  };

  useEffect(() => {
    if (!config.agentId) { setConnection('offline'); setError('Chat needs a configured agent ID.'); return; }
    const client = new Transport(config, {
      onMessage: (message) => {
        setMessages(previous => {
          const index = previous.findIndex(item => item.id === message.id);
          if (index < 0) return [...previous, message];
          return previous.map(item => item.id === message.id ? message : item);
        });
        if (message.role === 'assistant') { clearPending(); setError(''); }
      },
      onConnection: setConnection,
      onError: setError,
    });
    transport.current = client;
    void client.start().catch(() => setError('Unable to connect. Try sending again.'));
    return () => { clearTimeout(timeout.current); client.stop(); transport.current = null; };
  }, [config]);

  useEffect(() => {
    if (open) input.current?.focus();
    const escape = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && open) { setOpen(false); launcher.current?.focus(); }
    };
    document.addEventListener('keydown', escape);
    return () => document.removeEventListener('keydown', escape);
  }, [open]);
  useEffect(() => {
    if (log.current) log.current.scrollTop = log.current.scrollHeight;
  }, [messages, running, open]);

  async function send(text: string, id: string, optimistic = true) {
    if (!transport.current || pending.current) return;
    pending.current = true;
    setRunning(true);
    setError('');
    setFailed(undefined);
    if (optimistic) setMessages(previous => [...previous, { id, role: 'user', text }]);
    timeout.current = setTimeout(() => {
      clearPending();
      setError('The reply is taking longer than expected. You can send another message.');
    }, 60000);
    try { await transport.current.send(text, id); }
    catch { clearPending(); setFailed({ text, id }); setError('Message not sent. Please retry.'); }
  }
  const runtime = useExternalStoreRuntime<ChatMessage>({
    messages,
    isRunning: running,
    convertMessage: message => ({ id: message.id, role: message.role, content: [{ type: 'text', text: message.text }] }),
    onNew: async (message: AppendMessage) => {
      const text = message.content.filter(part => part.type === 'text').map(part => part.text).join('\n').trim();
      if (text) await send(text, crypto.randomUUID());
    },
  });
  function submit(event: FormEvent) {
    event.preventDefault();
    if (!draft.trim() || running || !config.agentId) return;
    runtime.thread.append(draft.trim());
    setDraft('');
  }
  const state = running ? 'think' : messages.length > 1 ? 'ready' : 'idle';
  const voice = (text: string) => config.theme === 'codepup' ? text.toUpperCase() : text;
  const style = { '--accent': config.accent, '--heart': themes[config.theme].heart } as CSSProperties;
  return <AssistantRuntimeProvider runtime={runtime}>
    <div className={`widget ${config.position}`} data-theme={config.theme} style={style}>
      {open && <section className="panel" role="dialog" aria-label={config.title}>
        <header><BrandIcon icon={config.icon} state={state} /><div className="heading"><strong>{voice(config.title)}</strong>
          <span className="connection" role="status"><i data-state={connection} />{connection === 'realtime' ? 'Connected' : connection === 'polling' ? 'Connected · polling' : connection === 'offline' ? 'Offline' : 'Connecting…'}</span></div>
          <button className="close" onClick={() => { setOpen(false); launcher.current?.focus(); }} aria-label="Close chat">×</button>
        </header>
        <div className="messages" ref={log} role="log" aria-label="Conversation" aria-live="off">
          <div className="intro">A LITTLE CONVERSATION, A LITTLE POSSIBILITY</div>
          {messages.map(message => <div key={message.id} className={`message ${message.role}`}>
            <span className="author">{message.role === 'assistant' ? voice(config.title) : voice('You')}</span>
            {message.role === 'assistant' ? <Reveal text={voice(message.text)} cps={config.streamCps} /> : <p>{message.text}</p>}
          </div>)}
          {running && <div className="typing" role="status" aria-label="Thinking"><span /><span /><span /></div>}
        </div>
        {error && <div className="error" role="alert">{error}{failed && <button onClick={() => void send(failed.text, failed.id, false)}>Retry</button>}</div>}
        <form onSubmit={submit}>
          <label className="sr-only" htmlFor="marina-message">Message</label>
          <textarea id="marina-message" ref={input} value={draft} placeholder={voice('Say something…')} rows={1} maxLength={8000}
            onChange={event => setDraft(event.target.value)} onKeyDown={event => {
              if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) { event.preventDefault(); submit(event); }
            }} />
          <button className="send" type="submit" aria-label="Send message" disabled={!draft.trim() || running || !config.agentId}>↑</button>
        </form>
        <footer>Thoughtfully connected <span aria-hidden="true">♥</span></footer>
      </section>}
      <button className="launcher" ref={launcher} aria-label={open ? 'Close chat' : `Open ${config.title} chat`} aria-expanded={open} onClick={() => setOpen(!open)}>
        <BrandIcon icon={config.icon} state={state} /><span className="launcher-dot" data-state={connection} />
      </button>
    </div>
  </AssistantRuntimeProvider>;
}
