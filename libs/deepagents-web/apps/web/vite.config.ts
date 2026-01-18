import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve, dirname } from 'path'
import { fileURLToPath } from 'url'

export default defineConfig(({ mode }) => {
  // Fix __dirname for ESM
  const __dirname = dirname(fileURLToPath(import.meta.url))
  
  // Load env from two levels up (libs/deepagents-web)
  const envDir = resolve(__dirname, '../../')
  const env = loadEnv(mode, envDir, '')
  
  const serverPort = parseInt(env.SERVER_PORT || '8005')
  const webPort = parseInt(env.WEB_PORT || '5173')
  const apiTarget = env.VITE_API_TARGET || `http://127.0.0.1:${serverPort}`

  return { 
    plugins: [vue()],
    // Tell Vite where to look for .env files
    envDir,
    server: { 
      port: webPort, 
      proxy: { 
        '/api/v1': { 
          target: apiTarget, 
          changeOrigin: true, 
          timeout: 600000 
        }
      } 
    } 
  }
})