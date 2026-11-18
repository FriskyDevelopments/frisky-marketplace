import { themes, type Theme } from './config';

const records: Record<string, unknown>[] = [];
const originalFetch = window.fetch;
window.fetch = async (input, options) => {
  const url = String(input);
  if (!url.includes('/demo-api/')) return originalFetch(input, options);
  const json = (value: unknown, status = 200) => new Response(JSON.stringify(value), { status, headers: { 'Content-Type': 'application/json' } });
  if (url.endsWith('/sessions')) return json({ conversation_id: 'demo-conversation' });
  if (url.endsWith('/realtime/connections')) return json({ error: { message: 'Demo uses polling' } }, 503);
  if (options?.method === 'POST') {
    const text = JSON.parse(String(options.body)).markdown_content;
    const message = { id: crypto.randomUUID(), conversation_id: 'demo-conversation', role: 'user', markdown_content: text };
    records.push(message);
    setTimeout(() => records.push({ id: crypto.randomUUID(), conversation_id: 'demo-conversation', role: 'assistant', markdown_content: 'There’s something lovely about a fresh start. Tell me a little more about what you have in mind, and we’ll find the next step together.' }), 1200);
    return json({ data: message });
  }
  return json({ data: { items: [...records], page_info: { has_next_page: false } } });
};
const requested = new URLSearchParams(location.search).get('theme') || 'marina';
const theme = Object.hasOwn(themes, requested) ? requested as Theme : 'marina';
if (new URLSearchParams(location.search).has('build')) {
  const script = document.createElement('script');
  script.src = '/dist/marina-chat.iife.js';
  Object.assign(script.dataset, { theme, agentId: 'local-demo', baseUrl: `${location.origin}/demo-api`, pollMs: '500' });
  document.body.append(script);
} else {
  const { mount } = await import('./index');
  mount({ theme, agentId: 'local-demo', baseUrl: `${location.origin}/demo-api`, pollMs: 500 });
}
