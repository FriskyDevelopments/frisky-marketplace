import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { readConfig } from './config';
import { Reveal } from './reveal';
import { Widget } from './Widget';
import { mount } from './index';

const mock = vi.hoisted(() => ({ send: vi.fn(async () => {}), stop: vi.fn(), callbacks: null as null | { onMessage: (message: {id: string; role: 'assistant'; text: string}) => void } }));
vi.mock('./transport', () => ({ Transport: class {
  constructor(_config: unknown, callbacks: typeof mock.callbacks) { mock.callbacks = callbacks; }
  start = vi.fn(async () => {});
  send = mock.send;
  stop = mock.stop;
} }));

let container: HTMLDivElement;
let root: Root;
beforeEach(() => {
  Object.assign(globalThis, { IS_REACT_ACT_ENVIRONMENT: true });
  vi.stubGlobal('matchMedia', vi.fn(() => ({ matches: false, addEventListener: vi.fn(), removeEventListener: vi.fn() })));
  container = document.createElement('div'); document.body.append(container); root = createRoot(container);
  mock.send.mockClear(); mock.stop.mockClear();
});
afterEach(async () => { await act(async () => root.unmount()); container.remove(); vi.unstubAllGlobals(); });

describe('widget interactions', () => {
  it('opens, sends through the external runtime, reveals a reply, and closes with Escape', async () => {
    await act(async () => root.render(<Widget config={readConfig(null, { agentId: 'agent' })} />));
    const launcher = container.querySelector<HTMLButtonElement>('.launcher')!;
    await act(async () => launcher.click());
    expect(container.querySelector('[role=dialog]')).not.toBeNull();
    const input = container.querySelector('textarea')!;
    expect(document.activeElement).toBe(input);
    await act(async () => {
      const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value')!.set!;
      setter.call(input, 'Hello');
      input.dispatchEvent(new Event('input', { bubbles: true }));
    });
    await act(async () => input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', shiftKey: true, bubbles: true })));
    expect(mock.send).not.toHaveBeenCalled();
    await act(async () => input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', isComposing: true, bubbles: true })));
    expect(mock.send).not.toHaveBeenCalled();
    await act(async () => input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true })));
    expect(mock.send).toHaveBeenCalledWith('Hello', expect.any(String));
    expect(container.querySelector('.typing')?.children).toHaveLength(3);
    expect(container.querySelector('.brand-icon.think')).not.toBeNull();
    await act(async () => mock.callbacks!.onMessage({ id: 'reply', role: 'assistant', text: 'A complete answer.' }));
    const reveal = container.querySelectorAll<HTMLButtonElement>('.reveal')[1];
    await act(async () => reveal.click());
    expect(reveal.textContent).toBe('A complete answer.');
    expect(container.querySelector('.brand-icon.ready')).not.toBeNull();
    await act(async () => document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true })));
    expect(container.querySelector('[role=dialog]')).toBeNull();
    expect(document.activeElement).toBe(launcher);
  });
  it('instantly reveals text for reduced motion and announces full text once', async () => {
    vi.stubGlobal('matchMedia', () => ({ matches: true, addEventListener: vi.fn(), removeEventListener: vi.fn() }));
    await act(async () => root.render(<Reveal text="A quiet response." cps={60} />));
    expect(container.querySelector('.reveal')?.textContent).toBe('A quiet response.');
    expect(container.querySelector('[aria-live=polite]')?.textContent).toBe('A quiet response.');
  });
  it('applies the uppercase Codepup voice and shows missing configuration', async () => {
    await act(async () => root.render(<Widget config={readConfig(null, { theme: 'codepup', greeting: 'hello friend' })} />));
    await act(async () => container.querySelector<HTMLButtonElement>('.launcher')!.click());
    expect(container.querySelector('[aria-live=polite]')?.textContent).toBe('HELLO FRIEND');
    expect(container.querySelector('[role=alert]')?.textContent).toContain('agent ID');
  });
  it('mounts styles inside Shadow DOM and tears down its transport', async () => {
    let chat: ReturnType<typeof mount>;
    await act(async () => { chat = mount({ agentId: 'agent' }); });
    expect(chat!.host.shadowRoot?.querySelector('style')?.textContent).toContain('#0d0d11');
    expect(chat!.host.shadowRoot?.querySelector('.launcher')).not.toBeNull();
    expect(chat!.host.querySelector('.launcher')).toBeNull();
    await act(async () => chat!.unmount());
    expect(chat!.host.isConnected).toBe(false);
    expect(mock.stop).toHaveBeenCalled();
  });
});
