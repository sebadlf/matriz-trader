import react from '@vitejs/plugin-react';
import { loadEnv } from 'vite';
import { defineConfig } from 'vitest/config';

// El único .env del monorepo vive en la raíz (AC-26).
const ENV_DIR = '..';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, ENV_DIR, '');

  return {
    envDir: ENV_DIR,
    plugins: [react()],
    server: {
      port: Number(env.FRONTEND_DEV_PORT || 5173),
      strictPort: true,
    },
    test: {
      environment: 'jsdom',
      setupFiles: ['./src/test/setup.ts'],
      // Un NODE_ENV=production heredado del shell cargaría el build de React sin `act`.
      env: { NODE_ENV: 'test' },
    },
  };
});
