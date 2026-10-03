import { readFileSync } from 'node:fs';
import { gzipSync } from 'node:zlib';

const bytes = gzipSync(readFileSync(new URL('../dist/marina-chat.iife.js', import.meta.url))).length;
console.log(`Standalone IIFE: ${(bytes / 1024).toFixed(1)} KiB gzip (${bytes} bytes)`);
if (bytes >= 150 * 1024) throw new Error('Widget exceeds the 150 KiB gzip budget');
