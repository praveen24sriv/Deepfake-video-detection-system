import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// The FastAPI backend serves the API under /api/v1 and analysis images under
// /outputs. Proxying both lets the browser call the backend same-origin, so no
// CORS configuration is needed in development (the backend's CORS list only
// allows http://localhost:5173).
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const target = env.VITE_PROXY_TARGET || 'http://127.0.0.1:8000'
  const proxy = {
    '/api': { target, changeOrigin: true },
    '/outputs': { target, changeOrigin: true },
  }

  return {
    plugins: [react()],
    server: { proxy },
    preview: { proxy },
  }
})
