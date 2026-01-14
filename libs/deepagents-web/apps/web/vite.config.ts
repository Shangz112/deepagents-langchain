import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
export default defineConfig({ 
  plugins: [vue()], 
  server: { 
    port: 5173, 
    proxy: { 
      '/api/v1': { 
        target: 'http://127.0.0.1:8005', 
        changeOrigin: true, 
        timeout: 600000 
      }
    } 
  } 
})