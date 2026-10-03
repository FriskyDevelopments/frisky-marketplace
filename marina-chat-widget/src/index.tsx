import { createRoot } from 'react-dom/client';
import { readConfig, type Config } from './config';
import { Widget } from './Widget';
import styles from './styles.css?inline';

export function mount(options?: Partial<Config>, container?: HTMLElement) {
  const config = readConfig(null, options);
  const host = container ?? document.createElement('marina-chat-widget');
  if (host.shadowRoot) throw new Error('Marina Chat is already mounted in this container');
  const shadow = host.attachShadow({ mode: 'open' });
  const style = document.createElement('style');
  style.textContent = styles;
  const target = document.createElement('div');
  shadow.append(style, target);
  if (!container) document.body.append(host);
  const root = createRoot(target);
  root.render(<Widget config={config} />);
  return { host, unmount() { root.unmount(); target.remove(); style.remove(); if (!container) host.remove(); } };
}

const script = document.currentScript as HTMLElement | null;
if (script) {
  const config = readConfig(script);
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', () => mount(config), { once: true });
  else mount(config);
}
