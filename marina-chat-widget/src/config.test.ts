import { describe, expect, it } from 'vitest';
import { readConfig, themes } from './config';
import { revealedText } from './reveal';

describe('configuration', () => {
  it('has exactly the requested presets', () => {
    expect(Object.keys(themes)).toEqual(['marina', 'codepup', 'nebu']);
    expect(readConfig(null, { theme: 'marina' }).accent).toBe('#9B3FB0');
    expect(readConfig(null, { theme: 'codepup' }).accent).toBe('#ff006b');
    expect(readConfig(null, { theme: 'nebu' }).title).toContain('Ashy');
  });
  it('gives data attributes priority over global options', () => {
    const script = document.createElement('script');
    Object.assign(script.dataset, { agentId: 'visitor-agent', title: 'Hello', theme: 'codepup', position: 'left', streamCps: '90', pollMs: '1000', baseUrl: 'https://proxy.example/v1/' });
    expect(readConfig(script, { title: 'Global', accent: '#abcdef' })).toMatchObject({ agentId: 'visitor-agent', title: 'Hello', theme: 'codepup', accent: '#abcdef', position: 'left', streamCps: 90, pollMs: 1000, baseUrl: 'https://proxy.example/v1' });
  });
  it('rejects unsafe URLs and sanitizes invalid themes, colors, and rates', () => {
    const script = document.createElement('script');
    Object.assign(script.dataset, { theme: 'fenrir', accent: 'red;display:none', streamCps: '-5', pollMs: 'NaN' });
    expect(readConfig(script)).toMatchObject({ theme: 'marina', accent: '#9B3FB0', streamCps: 60, pollMs: 2500 });
    expect(() => readConfig(null, { baseUrl: 'javascript:alert(1)' })).toThrow('HTTP(S)');
  });
});

describe('word reveal', () => {
  it('reveals whole words at the configured character rate', () => {
    expect(revealedText('Hello world!', 0, 60)).toBe('');
    expect(revealedText('Hello world!', 100, 60)).toBe('Hello ');
    expect(revealedText('Hello world!', 200, 60)).toBe('Hello world!');
  });
  it('caps long messages at four seconds and handles empty text', () => {
    const text = 'long message '.repeat(100);
    expect(revealedText(text, 3999, 60)).not.toBe(text);
    expect(revealedText(text, 4000, 60)).toBe(text);
    expect(revealedText('', 0, 60)).toBe('');
  });
});
