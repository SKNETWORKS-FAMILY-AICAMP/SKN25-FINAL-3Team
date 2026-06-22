import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Vite 서버 사이드 프록시: Docker 내부에서는 컨테이너 이름으로 라우팅됨
const FASTAPI_URL = process.env.FASTAPI_URL ?? 'http://localhost:8001'
const DJANGO_URL  = process.env.DJANGO_URL  ?? 'http://localhost:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,   // 0.0.0.0 — Docker 컨테이너 외부에서 접근 가능
    port: 3000,
    proxy: {
      '/api/v1/workspace': {
        target: DJANGO_URL,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/v1/, ''),
      },
      '/api': {
        target: FASTAPI_URL,
        changeOrigin: true,
      },
      '/auth': {
        target: DJANGO_URL,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/auth/, ''),
      },
    },
  },
  resolve: {
    alias: { '@': '/src' },
  },
})
