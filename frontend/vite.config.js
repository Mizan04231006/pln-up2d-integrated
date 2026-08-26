import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// API dipanggil lewat path relatif "/api/..." (same-origin).
// Di local dev, Vite mem-proxy permintaan /api/* ke backend FastAPI (uvicorn)
// sehingga frontend tetap 'npm run dev' dan backend tetap 'uvicorn main:app'
// tanpa perlu menyetel API_BASE manual.
const DEV_API_TARGET = process.env.VITE_API_TARGET || 'http://127.0.0.1:8000';

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': {
        target: DEV_API_TARGET,
        changeOrigin: true,
      },
    },
  },
});
