<template>
  <div class="h-full flex flex-col gap-2">
    <!-- Config Section -->
    <div class="panel border border-slate-700 rounded-lg overflow-hidden">
      <button class="w-full p-3 flex justify-between items-center bg-slate-800/50 hover:bg-slate-800 transition-colors" @click="toggle('config')">
        <span class="font-bold text-sm">参数配置</span>
        <span class="text-xs text-slate-500">{{ openSections.config ? '▼' : '▶' }}</span>
      </button>
      <div v-if="openSections.config" class="p-3 grid gap-3 text-sm animate-in slide-in-from-top-2">
        <div class="grid gap-1">
          <label class="text-xs text-slate-500">Model</label>
          <select v-model="sessionStore.config.model" class="input w-full text-xs bg-[#0b0f14]" @change="saveConfig">
            <option value="deepseek-ai/DeepSeek-V3.2">DeepSeek V3</option>
            <option value="deepseek-ai/DeepSeek-Coder-V2">DeepSeek Coder</option>
            <option value="Qwen/Qwen2.5-72B-Instruct">Qwen 2.5 72B</option>
            <option value="Qwen/Qwen2.5-Coder-32B-Instruct">Qwen 2.5 Coder</option>
          </select>
        </div>
        <div class="grid gap-1">
          <label class="text-xs text-slate-500">System Prompt</label>
          <select v-model="sessionStore.config.system_prompt" class="input w-full text-xs bg-[#0b0f14]" @change="saveConfig">
             <option :value="undefined">Default (Agent Instructions)</option>
             <option v-for="p in promptStore.prompts" :key="p.id" :value="p.content">{{ p.name }}</option>
          </select>
        </div>
        <div class="grid gap-1">
          <label class="text-xs text-slate-500">Temperature: {{ sessionStore.config.temperature }}</label>
          <input type="range" min="0" max="1" step="0.1" v-model.number="sessionStore.config.temperature" class="w-full accent-accent" @change="saveConfig" />
        </div>
        <div class="flex items-center justify-between">
          <span class="text-xs text-slate-500">Middleware</span>
          <label class="pill text-[10px] cursor-pointer">
            <input type="checkbox" v-model="sessionStore.config.middleware_enabled" class="mr-1" @change="saveConfig" /> Enabled
          </label>
        </div>
      </div>
    </div>

    <!-- Context Section -->
    <div class="panel border border-slate-700 rounded-lg overflow-hidden flex-1 flex flex-col min-h-0">
      <button class="w-full p-3 flex justify-between items-center bg-slate-800/50 hover:bg-slate-800 transition-colors" @click="toggle('context')">
        <span class="font-bold text-sm">会话上下文</span>
        <span class="text-xs text-slate-500">{{ openSections.context ? '▼' : '▶' }}</span>
      </button>
      <div v-if="openSections.context" class="p-3 overflow-y-auto custom-scrollbar flex-1 animate-in slide-in-from-top-2">
        <div class="text-xs text-slate-400 mb-2">Memory Summary</div>
        <div class="p-2 bg-[#0b0f14] rounded text-xs text-slate-300 leading-relaxed border border-slate-800">
          {{ sessionStore.memorySummary || '暂无记忆摘要...' }}
        </div>
        <div class="mt-3 text-xs text-slate-400 mb-2">History ({{ sessionStore.history?.length || 0 }})</div>
        <div class="grid gap-2">
          <div v-for="(h, idx) in sessionStore.history" :key="idx" class="p-2 rounded bg-slate-800/30 border border-slate-700/50 text-xs truncate">
            <span class="text-accent font-mono mr-1">[{{ h.role }}]</span> {{ h.content }}
          </div>
        </div>
      </div>
    </div>

    <!-- Logs Section -->
    <div class="panel border border-slate-700 rounded-lg overflow-hidden flex-1 flex flex-col min-h-0">
      <button class="w-full p-3 flex justify-between items-center bg-slate-800/50 hover:bg-slate-800 transition-colors" @click="toggle('logs')">
        <span class="font-bold text-sm">工具日志</span>
        <span class="text-xs text-slate-500">{{ openSections.logs ? '▼' : '▶' }}</span>
      </button>
      <div v-if="openSections.logs" class="p-3 overflow-y-auto custom-scrollbar flex-1 animate-in slide-in-from-top-2">
        <div v-if="!sessionStore.logs?.length" class="text-center text-xs text-slate-600 py-4">无日志记录</div>
        <div v-for="log in sessionStore.logs" :key="log.id" class="mb-2 p-2 rounded bg-[#0b0f14] border border-slate-800 text-[10px] font-mono">
          <div class="flex justify-between text-slate-500 mb-1">
            <span>{{ log.time }}</span>
            <span :class="log.status === 'error' ? 'text-red-400' : 'text-emerald-400'">{{ log.status }}</span>
          </div>
          <div class="text-slate-300 break-all">{{ log.msg }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, onMounted, onUnmounted, watch } from 'vue'
import axios from 'axios'
import { sessionStore, promptStore } from '../store'

const openSections = reactive({
  config: true,
  context: true,
  logs: true
})

function toggle(sec: keyof typeof openSections) {
  openSections[sec] = !openSections[sec]
}

async function loadSessionData() {
  if (!sessionStore.sessionId) return
  
  try {
    // Load Config
    const cfgRes = await axios.get(`/api/v1/chat/sessions/${sessionStore.sessionId}/config`)
    sessionStore.setConfig(cfgRes.data)
    
    // Load Context (History + Logs + Summary)
    const ctxRes = await axios.get(`/api/v1/chat/sessions/${sessionStore.sessionId}/context`)
    if (ctxRes.data) {
      sessionStore.setSummary(ctxRes.data.memorySummary)
      sessionStore.setHistory(ctxRes.data.history || [])
      sessionStore.logs = ctxRes.data.logs || []
    }
  } catch (e: any) {
    // Suppress common network interruption errors to avoid console spam
    // ERR_NETWORK_IO_SUSPENDED and ERR_ABORTED are browser-level errors that might appear in e.message or e.code
    // axios.isCancel(e) checks for cancellation
    const isNetworkError = 
        e.code === 'ERR_NETWORK_IO_SUSPENDED' || 
        e.code === 'ERR_ABORTED' || 
        e.code === 'ECONNABORTED' || 
        e.message === 'Network Error' ||
        e.message === 'canceled' ||
        axios.isCancel(e) ||
        (e.name === 'CanceledError');

    if (isNetworkError) {
        // Use debug level so it doesn't clutter the console unless verbose logging is on
        console.debug('Network interrupted during sync (retrying...)', e.message)
        return
    }
    console.error('Failed to load session data', e)
    
    // Reset session if not found
    if (e.response?.status === 404) {
      sessionStore.sessionId = null
    }
  }
}

async function saveConfig() {
  if (!sessionStore.sessionId) return
  try {
    await axios.post(`/api/v1/chat/sessions/${sessionStore.sessionId}/config`, sessionStore.config)
  } catch (e: any) {
    if (axios.isCancel(e) || e.message === 'Network Error' || e.code === 'ERR_NETWORK') {
         console.debug('Config save interrupted', e.message)
         return
    }
    console.error('Failed to save config', e)
  }
}

// Watch for session ID changes
watch(() => sessionStore.sessionId, (newId) => {
  if (newId) {
    loadSessionData()
  }
})

let pollTimer: number | undefined

async function poll() {
    if (sessionStore.sessionId) {
        await loadSessionData()
    }
    // Schedule next poll only after current one finishes
    pollTimer = window.setTimeout(poll, 3000)
}

onMounted(() => {
  promptStore.loadPrompts()
  poll()
})

onUnmounted(() => {
  if (pollTimer) clearTimeout(pollTimer)
})
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #334155; border-radius: 2px; }
</style>