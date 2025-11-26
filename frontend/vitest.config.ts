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
        statements: 75,
        branches: 70,
        functions: 70,
        lines: 75,
      },
      exclude: ['src/main.tsx', 'src/types.ts'],
    },
  },
});
