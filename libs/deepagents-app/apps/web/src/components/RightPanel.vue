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
          <select class="input w-full text-xs bg-[#0b0f14]">
            <option>gpt-4-turbo</option>
            <option>claude-3-opus</option>
            <option>llama-3-70b</option>
          </select>
        </div>
        <div class="grid gap-1">
          <label class="text-xs text-slate-500">Temperature: {{ config.temp }}</label>
          <input type="range" min="0" max="1" step="0.1" v-model="config.temp" class="w-full accent-accent" />
        </div>
        <div class="flex items-center justify-between">
          <span class="text-xs text-slate-500">Middleware</span>
          <label class="pill text-[10px] cursor-pointer">
            <input type="checkbox" v-model="config.middleware" class="mr-1" /> Enabled
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
          {{ memorySummary || '暂无记忆摘要...' }}
        </div>
        <div class="mt-3 text-xs text-slate-400 mb-2">History ({{ historyCount }})</div>
        <div class="grid gap-2">
          <div v-for="h in history" :key="h.id" class="p-2 rounded bg-slate-800/30 border border-slate-700/50 text-xs truncate">
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
        <div v-if="logs.length === 0" class="text-center text-xs text-slate-600 py-4">无日志记录</div>
        <div v-for="log in logs" :key="log.id" class="mb-2 p-2 rounded bg-[#0b0f14] border border-slate-800 text-[10px] font-mono">
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
import { reactive, ref } from 'vue'

const openSections = reactive({
  config: true,
  context: true,
  logs: true
})

const config = reactive({
  temp: 0.7,
  middleware: true
})

const memorySummary = ref('用户正在进行前端重构任务，要求使用 React/Vue + TS，并遵循扁平化设计原则。')
const historyCount = ref(12)
const history = ref([
  { id: 1, role: 'user', content: '开始前端重构' },
  { id: 2, role: 'assistant', content: '好的，请提供详细需求' },
  { id: 3, role: 'user', content: '参考以下设计原则...' }
])

const logs = ref([
  { id: 1, time: '10:00:01', status: 'info', msg: 'Session initialized' },
  { id: 2, time: '10:00:02', status: 'success', msg: 'Tool [Search] executed in 1200ms' }
])

function toggle(sec: keyof typeof openSections) {
  openSections[sec] = !openSections[sec]
}
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #334155; border-radius: 2px; }
</style>