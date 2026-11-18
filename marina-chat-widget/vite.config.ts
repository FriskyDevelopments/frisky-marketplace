import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig(({ command }) => ({
  plugins: [react()],
  define: command === 'build' ? { 'process.env.NODE_ENV': JSON.stringify('production') } : {},
  build: {
    target: 'es2022',
    lib: {
      entry: 'src/index.tsx',
      name: 'MarinaChat',
      formats: ['iife', 'es'],
      fileName: (format) => `marina-chat.${format === 'iife' ? 'iife.js' : 'js'}`,
    },
  },
  test: { environment: 'jsdom', restoreMocks: true, css: true },
}));
