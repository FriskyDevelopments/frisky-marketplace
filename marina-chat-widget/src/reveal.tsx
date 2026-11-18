import { useEffect, useState } from 'react';

export function revealedText(text: string, elapsed: number, cps: number): string {
  const duration = Math.min(4000, text.length / cps * 1000);
  if (elapsed >= duration) return text;
  const limit = Math.floor(text.length * elapsed / duration);
  const words = [...text.matchAll(/\S+\s*/gu)];
  let end = 0;
  for (const word of words) {
    const next = word.index + word[0].length;
    if (next > limit) break;
    end = next;
  }
  return text.slice(0, end);
}

export function Reveal({ text, cps }: { text: string; cps: number }) {
  const [visible, setVisible] = useState('');
  const [skip, setSkip] = useState(false);
  const [reduced, setReduced] = useState(() => matchMedia('(prefers-reduced-motion: reduce)').matches);
  useEffect(() => {
    const media = matchMedia('(prefers-reduced-motion: reduce)');
    const change = () => setReduced(media.matches);
    media.addEventListener('change', change);
    return () => media.removeEventListener('change', change);
  }, []);
  useEffect(() => {
    if (skip || reduced) { setVisible(text); return; }
    const start = performance.now();
    let frame: number;
    const tick = () => {
      const next = revealedText(text, performance.now() - start, cps);
      setVisible(next);
      if (next !== text) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [text, cps, skip, reduced]);
  const complete = visible === text;
  return <>
    <span className="sr-only" aria-live="polite" aria-atomic="true">{text}</span>
    <button className="reveal" type="button" aria-label={complete ? 'Assistant message' : 'Show complete assistant message'} onClick={() => setSkip(true)}>
      <span aria-hidden="true">{visible || '\u00a0'}</span>
    </button>
  </>;
}
