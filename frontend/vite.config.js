import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

// El navegador utiliza /api; Vite reenvía la petición a FastAPI.
export default defineConfig(({ mode }) => {
  const env = { ...loadEnv(mode, process.cwd(), ''), ...process.env };
  const apiProxy = {
    '/api': { target: env.API_PROXY_TARGET || 'http://127.0.0.1:8000' },
  };

  return {
    plugins: [react()],
    server: { port: Number(env.FRONTEND_PORT || 5173), strictPort: true, proxy: apiProxy },
    preview: { port: 4173, strictPort: true, proxy: apiProxy },
  };
});
