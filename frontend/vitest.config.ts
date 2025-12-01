import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    globals: true,
    css: true,
    coverage: {
      provider: 'v8',
      thresholds: {
        statements: 70,
        branches: 70,
        functions: 70,
        lines: 70,
      },
      exclude: [
        'src/main.tsx',
        'src/types.ts',
        'vite.config.ts',
        'vitest.config.ts',
        'playwright.config.ts',
        'src/vite-env.d.ts',
        'e2e/**',
      ],
    },
    exclude: ['e2e/**', 'node_modules/**'],
  },
});
