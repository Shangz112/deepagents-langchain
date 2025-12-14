import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
export default defineConfig({ 
  plugins: [vue()], 
  server: { 
    port: 5173, 
    proxy: { 
      '/api/v1/chat': { 
        target: 'http://127.0.0.1:8002', 
        changeOrigin: true, 
        rewrite: (path) => path.replace(/^\/api\/v1\/chat/, ''),
        timeout: 600000 
      },
      '/api/v1': { 
        target: 'http://127.0.0.1:8002', 
        changeOrigin: true, 
        rewrite: (path) => path.replace(/^\/api\/v1/, ''),
        timeout: 600000 
      }
    } 
  } 
})