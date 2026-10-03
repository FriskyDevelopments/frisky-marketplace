export const themes = {
  marina: { accent: '#9B3FB0', heart: '#C9A24B', title: 'Marina', greeting: 'Hola, I’m Marina. What’s on your mind?', icon: 'bugambilia' },
  codepup: { accent: '#ff006b', heart: '#ff006b', title: 'CODEPUP', greeting: 'HEY, I’M CODEPUP. WHAT ARE WE BUILDING?', icon: 'pup' },
  nebu: { accent: '#a89bc9', heart: '#8a929e', title: 'Ashy · Nebu', greeting: 'A little clarity, a little space. How can I help?', icon: 'star' },
} as const;

export type Theme = keyof typeof themes;
export interface Config {
  agentId: string;
  baseUrl: string;
  theme: Theme;
  title: string;
  accent: string;
  icon: string;
  greeting: string;
  position: 'left' | 'right';
  streamCps: number;
  pollMs: number;
}

declare global {
  interface Window { MarinaChatConfig?: Partial<Config> }
}

function positive(value: unknown, fallback: number, min: number, max: number) {
  const number = Number(value);
  return Number.isFinite(number) && number > 0 ? Math.min(max, Math.max(min, number)) : fallback;
}

export function readConfig(script?: HTMLElement | null, global = window.MarinaChatConfig): Config {
  const input: Record<string, unknown> = { ...global, ...script?.dataset };
  const theme: Theme = Object.hasOwn(themes, String(input.theme)) ? input.theme as Theme : 'marina';
  const preset = themes[theme];
  const url = new URL(String(input.baseUrl || '/api/marina-chat'), window.location.href);
  if (!['http:', 'https:'].includes(url.protocol)) throw new Error('Marina Chat requires an HTTP(S) proxy URL');
  const accent = String(input.accent || preset.accent);
  return {
    agentId: String(input.agentId || ''),
    baseUrl: url.href.replace(/\/$/, ''),
    theme,
    title: String(input.title || preset.title),
    accent: /^#[\da-f]{3,8}$/i.test(accent) && [4, 5, 7, 9].includes(accent.length) ? accent : preset.accent,
    icon: String(input.icon || preset.icon),
    greeting: String(input.greeting || preset.greeting),
    position: input.position === 'left' ? 'left' : 'right',
    streamCps: positive(input.streamCps, 60, 1, 1000),
    pollMs: positive(input.pollMs, 2500, 500, 60000),
  };
}
