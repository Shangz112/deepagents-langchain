<template>
  <div class="h-full flex flex-col relative bg-[var(--bg-app)]">
    <!-- Top Bar & Tabs (Redesigned) -->
    <div class="flex items-center justify-between px-6 py-3 border-b border-[var(--border-subtle)] bg-[var(--bg-panel)]/80 backdrop-blur-md z-10 shrink-0 h-[60px] shadow-sm">
      
      <!-- Left: Title & View Switcher -->
      <div class="flex items-center gap-6">
        <h2 class="text-lg font-bold text-[var(--fg-primary)] tracking-tight hidden md:block">
            {{ activeTab === 'Chat' ? 'DeepAgent' : activeTab }}
        </h2>
        
        <div class="flex bg-[var(--bg-surface)] rounded-lg p-1 border border-[var(--border-subtle)]">
            <button 
              v-for="tab in tabs" 
              :key="tab.id"
              class="flex items-center gap-2 px-3 py-1 text-xs font-medium rounded-md transition-all duration-200"
              :class="activeTab === tab.id ? 'bg-[var(--bg-app)] text-[var(--accent-primary)] shadow-sm' : 'text-[var(--fg-tertiary)] hover:text-[var(--fg-secondary)]'"
              @click="activeTab = tab.id"
            >
              <Icon :name="tab.icon" size="14" />
              {{ tab.label }}
            </button>
        </div>
      </div>
      
      <!-- Right: Session Status -->
      <div class="flex items-center gap-3">
        <div class="h-4 w-px bg-[var(--border-subtle)]"></div>
        <div class="flex items-center gap-2 text-xs">
          <div class="flex items-center gap-1.5 px-2 py-1 rounded-full bg-[var(--bg-surface)] border border-[var(--border-subtle)] transition-colors hover:border-[var(--accent-primary)]/30">
             <span class="relative flex h-2 w-2">
              <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" :class="sessionError ? 'bg-red-400' : 'bg-emerald-400'"></span>
              <span class="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" :class="sessionError ? 'bg-red-500' : 'bg-emerald-500'"></span>
            </span>
            <span class="font-medium text-[var(--fg-secondary)]" :class="sessionError ? 'text-[var(--error)]' : ''">Session</span>
            <span class="font-mono text-[var(--fg-primary)] ml-1 cursor-pointer hover:text-[var(--accent-primary)]" @click="() => ensureSession()">
                {{ sessionId ? sessionId.slice(0,8) : (sessionError ? 'Retry' : 'Init...') }}
            </span>
          </div>
          <button class="p-1.5 text-[var(--fg-tertiary)] hover:text-[var(--fg-primary)] hover:bg-[var(--bg-hover)] rounded-md transition-colors" title="Export Dataset" @click="exportDataset">
            <Icon name="download" size="16" />
          </button>
          <button class="p-1.5 text-[var(--fg-tertiary)] hover:text-[var(--fg-primary)] hover:bg-[var(--bg-hover)] rounded-md transition-colors" title="Session Settings">
            <Icon name="settings" size="16" />
          </button>
        </div>
      </div>
    </div>

    <!-- Main Content Area -->
    <div class="flex-1 overflow-hidden relative">
      
      <!-- Chat View -->
      <div v-show="activeTab === 'Chat'" class="h-full flex flex-col min-h-0 relative">
        
        <!-- Welcome Screen (Bisheng Style) -->
        <div v-if="chatStore.messages.length === 0" class="flex-1 z-0 flex flex-col items-center p-8 text-center select-none animate-in fade-in zoom-in duration-500">
            
            <!-- Center Content -->
            <div class="flex-1 flex flex-col items-center justify-center w-full">
                <div class="w-20 h-20 rounded-2xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white mb-8 shadow-2xl shadow-blue-500/20 ring-4 ring-white/10">
                   <Icon name="zap" size="40" />
                </div>
                <h2 class="text-2xl font-bold text-[var(--fg-primary)] mb-4">我是 DeepAgent，很高兴见到你！</h2>
                <p class="text-[var(--fg-secondary)] max-w-lg leading-relaxed text-sm">
                   欢迎体验新一代 Agent 助理。擅长完成复杂任务，您可以直接下达指令，或描述您的目标，我会自动拆解任务、调用工具并逐步执行。
                </p>
            </div>
            
            <!-- Quick Starters -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 w-full max-w-2xl shrink-0 mb-2">
               <button @click="quickStart('帮我写一个 Python 贪吃蛇游戏')" class="p-4 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-panel)] hover:border-[var(--accent-primary)] hover:shadow-lg hover:-translate-y-1 transition-all text-left group">
                  <div class="font-medium text-[var(--fg-primary)] mb-1 group-hover:text-[var(--accent-primary)] flex items-center gap-2">
                    <span class="text-xl">🐍</span> Python 贪吃蛇
                  </div>
                  <div class="text-xs text-[var(--fg-tertiary)]">编写一个完整的贪吃蛇游戏代码</div>
               </button>
               <button @click="quickStart('分析当前目录下的代码结构')" class="p-4 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-panel)] hover:border-[var(--accent-primary)] hover:shadow-lg hover:-translate-y-1 transition-all text-left group">
                  <div class="font-medium text-[var(--fg-primary)] mb-1 group-hover:text-[var(--accent-primary)] flex items-center gap-2">
                    <span class="text-xl">📂</span> 代码分析
                  </div>
                  <div class="text-xs text-[var(--fg-tertiary)]">阅读并解释当前项目架构</div>
               </button>
               <button @click="quickStart('搜索最新的 AI Agent 发展趋势')" class="p-4 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-panel)] hover:border-[var(--accent-primary)] hover:shadow-lg hover:-translate-y-1 transition-all text-left group">
                  <div class="font-medium text-[var(--fg-primary)] mb-1 group-hover:text-[var(--accent-primary)] flex items-center gap-2">
                    <span class="text-xl">🔍</span> 联网搜索
                  </div>
                  <div class="text-xs text-[var(--fg-tertiary)]">查询最新的技术动态</div>
               </button>
               <button @click="quickStart('制定一个学习 Rust 语言的计划')" class="p-4 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-panel)] hover:border-[var(--accent-primary)] hover:shadow-lg hover:-translate-y-1 transition-all text-left group">
                  <div class="font-medium text-[var(--fg-primary)] mb-1 group-hover:text-[var(--accent-primary)] flex items-center gap-2">
                    <span class="text-xl">📅</span> 学习计划
                  </div>
                  <div class="text-xs text-[var(--fg-tertiary)]">生成详细的学习路线图</div>
               </button>
            </div>
        </div>

        <MessageList 
          v-else
          class="flex-1 z-10"
          :messages="chatStore.messages" 
          @retry-tool="retryTool" 
          @debug-tool="debugTool" 
        />
        
        <div class="shrink-0 p-6 border-t border-[var(--border-subtle)] bg-[var(--bg-panel)]/50 backdrop-blur-sm z-20">
          <Composer class="max-w-4xl mx-auto shadow-2xl rounded-xl overflow-hidden border border-[var(--border-subtle)]" @send="onSend" />
        </div>
      </div>
      
      <!-- Task View -->
      <div v-show="activeTab === 'Task'" class="h-full p-6 overflow-y-auto bg-[var(--bg-app)]">
        <div class="max-w-3xl mx-auto space-y-6">
           <div class="panel-card p-6 shadow-lg relative overflow-hidden">
             <!-- Background Decor -->
             <div class="absolute top-0 right-0 p-16 bg-[var(--accent-primary)]/5 blur-3xl rounded-full -translate-y-1/2 translate-x-1/2 pointer-events-none"></div>

             <div class="flex items-center justify-between mb-8 relative">
               <div>
                 <h3 class="text-lg font-bold text-[var(--fg-primary)] flex items-center gap-2">
                   <Icon name="layers" size="20" class="text-[var(--accent-primary)]" />
                   Execution Plan
                 </h3>
                 <p class="text-sm text-[var(--fg-tertiary)] mt-1">Real-time agent reasoning and task breakdown</p>
               </div>
               <span class="text-xs font-mono text-[var(--fg-tertiary)] px-2 py-1 rounded bg-[var(--bg-app)] border border-[var(--border-subtle)]">ID: {{ sessionId ? sessionId.slice(0,8) : '---' }}</span>
             </div>
             
             <div class="relative pl-4 border-l-2 border-[var(--border-subtle)] space-y-8 ml-2">
               <div v-if="tasks.length === 0" class="text-[var(--fg-tertiary)] text-sm italic pl-6">
                 No tasks executed yet. Start a conversation to see the execution plan.
               </div>
               <div v-for="(t, index) in tasks" :key="t.id" 
                 class="group relative pl-6 transition-all duration-300"
               >
                 <!-- Timeline Node -->
                 <div 
                    class="absolute -left-[21px] top-0 w-10 h-10 rounded-full border-4 border-[var(--bg-panel)] flex items-center justify-center transition-all duration-300 z-10"
                    :class="getTimelineNodeClass(t.status)"
                 >
                    <Icon v-if="t.status === 'completed'" name="check" size="14" />
                    <Icon v-else-if="t.status === 'failed'" name="alert-circle" size="14" />
                    <div v-else-if="t.status === 'in_progress'" class="w-2 h-2 bg-current rounded-full animate-pulse"></div>
                    <span v-else class="text-[10px] font-bold text-[var(--fg-tertiary)]">{{ index + 1 }}</span>
                 </div>

                 <!-- Content -->
                 <div 
                    class="p-4 rounded-lg border transition-all duration-300 hover:shadow-md"
                    :class="getTaskCardClass(t.status)"
                 >
                   <div class="flex justify-between items-start mb-1">
                     <div class="font-medium text-base" :class="t.status === 'completed' ? 'text-[var(--fg-secondary)]' : 'text-[var(--fg-primary)]'">{{ t.title }}</div>
                     <span class="text-[10px] uppercase tracking-wider font-bold px-2 py-0.5 rounded-full border"
                       :class="getStatusBadgeClass(t.status)"
                     >
                       {{ t.status.replace('_', ' ') }}
                     </span>
                   </div>
                   <div class="text-xs text-[var(--fg-tertiary)] mt-1 flex items-center gap-2">
                      <span v-if="t.status === 'in_progress'" class="flex items-center gap-1 text-[var(--accent-primary)]">
                        <Icon name="refresh-cw" size="10" class="animate-spin" /> Processing
                      </span>
                      <span v-else>Step {{ index + 1 }}</span>
                   </div>
                   <!-- Input/Output Preview -->
                   <div v-if="t.input" class="mt-3 pt-3 border-t border-[var(--border-subtle)]/50">
                      <div class="text-[10px] uppercase font-bold text-[var(--fg-tertiary)] mb-1">Input</div>
                      <pre class="text-xs font-mono bg-[var(--bg-app)]/50 p-2 rounded text-[var(--fg-secondary)] overflow-x-auto">{{ JSON.stringify(t.input, null, 2) }}</pre>
                   </div>
                 </div>
               </div>
             </div>
           </div>
        </div>
      </div>

      <!-- Plan View -->
      <div v-show="activeTab === 'Plan'" class="h-full relative bg-[var(--bg-app)]">
        <PlanGraph :messages="chatStore.messages" />
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, computed } from 'vue'
import axios from 'axios'
import { sessionStore, chatStore } from '../store'
import MessageList from '../components/chat/MessageList.vue'
import Composer from '../components/chat/Composer.vue'
import PlanGraph from './PlanGraph.vue'
import Icon from '../components/common/Icon.vue'

const activeTab = ref('Chat')
const sessionId = ref<string | null>(null)
const sessionError = ref<boolean>(false)
let currentEventSource: EventSource | null = null
const quickStarters = ref<any[]>([])

onMounted(async () => {
    try {
        const r = await axios.get('/api/v1/prompts/quick-starters')
        quickStarters.value = r.data
    } catch (e) {
        console.error('Failed to load quick starters', e)
        quickStarters.value = []
    }
})

const tabs = [
  { id: 'Chat', label: 'Chat', icon: 'message-square' },
  { id: 'Task', label: 'Tasks', icon: 'layers' },
  { id: 'Plan', label: 'Graph', icon: 'activity' },
]

const tasks = computed(() => {
  const allTasks: any[] = []
  chatStore.messages.forEach(msg => {
    if (msg.role === 'assistant' && msg.toolEvents) {
      msg.toolEvents.forEach((tool: any) => {
        allTasks.push({
          id: tool.id,
          title: `Execute tool: ${tool.name}`,
          status: tool.status,
          timestamp: tool.timestamp,
          input: tool.input
        })
      })
    }
  })
  return allTasks
})

function getTimelineNodeClass(status: string) {
  switch (status) {
    case 'completed': return 'bg-[var(--success)] text-white border-[var(--bg-panel)]'
    case 'failed': return 'bg-[var(--error)] text-white border-[var(--bg-panel)]'
    case 'in_progress': return 'bg-[var(--bg-panel)] text-[var(--accent-primary)] border-[var(--accent-primary)] shadow-[0_0_0_2px_var(--accent-glow)]'
    default: return 'bg-[var(--bg-surface)] text-[var(--fg-tertiary)] border-[var(--bg-panel)]'
  }
}

function getTaskCardClass(status: string) {
  switch (status) {
    case 'completed': return 'bg-[var(--bg-app)]/50 border-[var(--border-subtle)] opacity-75'
    case 'failed': return 'bg-[var(--error)]/5 border-[var(--error)]/30'
    case 'in_progress': return 'bg-[var(--accent-surface)]/10 border-[var(--accent-primary)]/30 shadow-sm'
    default: return 'bg-[var(--bg-app)] border-[var(--border-subtle)] border-dashed'
  }
}

function getStatusBadgeClass(status: string) {
  switch (status) {
    case 'completed': return 'bg-[var(--success)]/10 text-[var(--success)] border-[var(--success)]/20'
    case 'failed': return 'bg-[var(--error)]/10 text-[var(--error)] border-[var(--error)]/20'
    case 'in_progress': return 'bg-[var(--accent-surface)] text-[var(--accent-primary)] border-[var(--accent-primary)]/20'
    default: return 'bg-[var(--bg-hover)] text-[var(--fg-tertiary)] border-[var(--border-subtle)]'
  }
}

onMounted(() => ensureSession())

onMounted(() => {
  // Do not close stream here to allow background generation
  // if (currentEventSource) ...
})

async function ensureSession(retryCount = 0) {
  if (sessionId.value) return

  // Check if store already has a session
  if (sessionStore.sessionId) {
      sessionId.value = sessionStore.sessionId
      return
  }

  sessionError.value = false
  try {
    const r = await axios.post('/api/v1/chat/sessions')
    sessionId.value = r.data.id
    sessionStore.setSessionId(r.data.id)
    sessionError.value = false
  } catch (e) {
    console.error('Failed to init session', e)
    sessionError.value = true
    
    // Retry with exponential backoff up to 3 times automatically
    if (retryCount < 3) {
      const delay = Math.pow(2, retryCount) * 1000
      console.log(`Retrying session init in ${delay}ms...`)
      setTimeout(() => ensureSession(retryCount + 1), delay)
    }
  }
}

function quickStart(text: string) {
  onSend({ text, tools: true, files: [] })
}

async function onSend(payload: { text: string; tools: boolean; template?: any; files: File[] }) {
  if (!sessionId.value) {
      await ensureSession()
      if (!sessionId.value) {
        chatStore.messages.push({
          id: String(Date.now()),
          role: 'system',
          content: 'Error: Could not initialize session. Please check connection and try again.',
          timestamp: Date.now()
        })
        return
      }
  }

  await chatStore.sendMessage(payload, sessionId.value)
}

function retryTool(toolId: string) {
  console.log('Retrying tool', toolId)
}

function debugTool(toolId: string) {
  console.log('Debug tool', toolId)
}

async function exportDataset() {
    try {
        const r = await axios.get('/api/v1/feedback/export')
        // Trigger download
        const blob = new Blob([JSON.stringify(r.data, null, 2)], { type: 'application/json' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `dataset_export_${Date.now()}.json`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)
    } catch (e) {
        console.error('Failed to export dataset', e)
        alert('Failed to export dataset')
    }
}
</script>
