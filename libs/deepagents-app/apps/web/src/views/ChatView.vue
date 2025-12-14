<template>
  <div class="h-full flex flex-col relative bg-[var(--bg-app)]">
    <!-- Top Bar & Tabs -->
    <div class="flex items-center justify-between px-4 py-2 border-b border-[var(--border-subtle)] bg-[var(--bg-panel)]/80 backdrop-blur-md z-10 shrink-0 h-[56px] shadow-sm">
      
      <!-- Left: Tabs -->
      <div class="flex items-center gap-1 p-1 bg-[var(--bg-surface)] rounded-lg border border-[var(--border-subtle)]">
        <button 
          v-for="tab in tabs" 
          :key="tab.id"
          class="flex items-center gap-2 px-3 py-1.5 text-sm font-medium rounded-md transition-all duration-200"
          :class="activeTab === tab.id ? 'bg-[var(--bg-app)] text-[var(--fg-primary)] shadow-sm' : 'text-[var(--fg-tertiary)] hover:text-[var(--fg-secondary)] hover:bg-[var(--bg-hover)]/50'"
          @click="activeTab = tab.id"
        >
          <Icon :name="tab.icon" size="14" :class="activeTab === tab.id ? 'text-[var(--accent-primary)]' : 'currentColor'" />
          {{ tab.label }}
        </button>
      </div>
      
      <!-- Right: Session Status -->
      <div class="flex items-center gap-3">
        <div class="h-4 w-px bg-[var(--border-subtle)]"></div>
        <div class="flex items-center gap-2 text-xs">
          <div class="flex items-center gap-1.5 px-2 py-1 rounded-full bg-[var(--bg-surface)] border border-[var(--border-subtle)]">
             <span class="relative flex h-2 w-2">
              <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" :class="sessionError ? 'bg-red-400' : 'bg-emerald-400'"></span>
              <span class="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" :class="sessionError ? 'bg-red-500' : 'bg-emerald-500'"></span>
            </span>
            <span class="font-medium text-[var(--fg-secondary)]" :class="sessionError ? 'text-[var(--error)]' : ''">Session</span>
            <span class="font-mono text-[var(--fg-primary)] ml-1 cursor-pointer" @click="() => ensureSession()">
                {{ sessionId ? sessionId.slice(0,8) : (sessionError ? 'Retry' : 'Init...') }}
            </span>
          </div>
          <button class="p-1.5 text-[var(--fg-tertiary)] hover:text-[var(--fg-primary)] hover:bg-[var(--bg-hover)] rounded-md transition-colors" title="Session Settings">
            <Icon name="settings" size="16" />
          </button>
        </div>
      </div>
    </div>

    <!-- Main Content Area -->
    <div class="flex-1 overflow-hidden relative">
      
      <!-- Chat View -->
      <div v-show="activeTab === 'Chat'" class="h-full flex flex-col min-h-0">
        <MessageList 
          class="flex-1"
          :messages="messages" 
          @retry-tool="retryTool" 
          @debug-tool="debugTool" 
        />
        <div class="shrink-0 p-4 border-t border-[var(--border-subtle)] bg-[var(--bg-panel)]/50 backdrop-blur-sm">
          <Composer class="max-w-4xl mx-auto" @send="onSend" />
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
        <PlanGraph :messages="messages" />
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import axios from 'axios'
import MessageList from '../components/chat/MessageList.vue'
import Composer from '../components/chat/Composer.vue'
import PlanGraph from './PlanGraph.vue'
import Icon from '../components/common/Icon.vue'

const activeTab = ref('Chat')
const sessionId = ref<string | null>(null)
const sessionError = ref<boolean>(false)
const messages = ref<any[]>([])

const tabs = [
  { id: 'Chat', label: 'Chat', icon: 'message-square' },
  { id: 'Task', label: 'Tasks', icon: 'layers' },
  { id: 'Plan', label: 'Graph', icon: 'activity' },
]

const tasks = computed(() => {
  const allTasks: any[] = []
  messages.value.forEach(msg => {
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

async function ensureSession(retryCount = 0) {
  if (sessionId.value) return

  sessionError.value = false
  try {
    const r = await axios.post('/api/v1/chat/sessions')
    sessionId.value = r.data.id
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

async function onSend(payload: { text: string; tools: boolean; template?: any; files: File[] }) {
  if (!sessionId.value) {
      await ensureSession()
      // If still no session after one immediate attempt, fail
      if (!sessionId.value) {
         messages.value.push({
          id: String(Date.now()),
          role: 'system',
          content: 'Error: Could not initialize session. Please check connection and try again.',
          timestamp: Date.now()
        })
        return
      }
  }

  // Add User Message
  const userMsgId = String(Date.now())
  messages.value.push({ 
    id: userMsgId, 
    role: 'user', 
    content: payload.text, 
    timestamp: Date.now() 
  })

  try {
    await axios.post(`/api/v1/chat/sessions/${sessionId.value}/messages`, { 
      content: payload.text, 
      tools: payload.tools 
    })

    // Start SSE
    const es = new EventSource(`/api/v1/chat/sessions/${sessionId.value}/stream`)
    
    // Create placeholder for assistant message
    const assistantMsgId = String(Date.now() + 1)
    const assistantMsg = reactive({
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      reasoning: '', // Add reasoning field
      timestamp: Date.now(),
      streaming: true,
      toolEvents: [] as any[],
      isError: false
    })
    messages.value.push(assistantMsg)

    es.onmessage = e => {
      try {
        const d = JSON.parse(e.data)
        
        if (d.type === 'ping') {
           // Keep-alive
           return
        }

        if (d.type === 'reasoning') {
           assistantMsg.reasoning = (assistantMsg.reasoning || '') + (d.content || '')
        }
        
        if (d.type === 'message' || d.type === 'chunk') {
          assistantMsg.content += (d.content || '')
        }
        
        if (d.type === 'tool') {
          // Check if event exists
          const existingIdx = assistantMsg.toolEvents.findIndex((evt: any) => evt.id === d.id)
          if (existingIdx >= 0) {
             Object.assign(assistantMsg.toolEvents[existingIdx], d)
          } else {
             assistantMsg.toolEvents.push({
               id: d.id,
               name: d.name,
               status: d.status,
               input: d.input,
               output: d.output,
               timestamp: Date.now()
             })
          }
        }
        
        if (d.type === 'done') {
          assistantMsg.streaming = false
          es.close()
        }
      } catch (err) {
        console.error('SSE Parse Error', err)
      }
    }
    
    es.onerror = (e) => {
       // Only treat as error if we haven't finished properly and connection is truly closed
       if (es.readyState === EventSource.CLOSED) {
          if (assistantMsg.streaming) {
              console.error('SSE Error', e)
              assistantMsg.streaming = false
              if (!assistantMsg.content && !assistantMsg.reasoning) {
                   assistantMsg.content = "Error: Connection interrupted. Please try again."
                   assistantMsg.isError = true
              }
          }
       }
    }

  } catch (e) {
    console.error('Send failed', e)
    messages.value.push({
      id: String(Date.now()),
      role: 'system',
      content: 'Error sending message: ' + (e as Error).message,
      timestamp: Date.now()
    })
  }
}

function retryTool(toolId: string) {
  console.log('Retrying tool', toolId)
}

function debugTool(toolId: string) {
  console.log('Debug tool', toolId)
}
</script>
