<template>
  <div class="flex flex-col p-4 overflow-y-auto custom-scrollbar min-h-0" ref="container" @scroll="onScroll">
    <div v-for="msg in messages" :key="msg.id" 
      class="flex gap-4 w-full transition-all duration-300 mb-6"
      :class="msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'"
    >
      <!-- Avatar (Outside) -->
      <div class="shrink-0 w-10 h-10 rounded-full flex items-center justify-center shadow-sm border border-slate-200/50"
           :class="msg.role === 'user' ? 'bg-indigo-600 text-white' : 'bg-white text-blue-600'">
           <Icon :name="msg.role === 'user' ? 'user' : 'zap'" size="20" />
      </div>
      
      <!-- Content Group -->
      <div class="flex flex-col gap-1 max-w-[90%] md:max-w-[80%]" :class="msg.role === 'user' ? 'items-end' : 'items-start'">
          <!-- Name/Time -->
          <div class="text-[10px] text-slate-400 px-1 flex gap-2 items-center opacity-70">
             <span class="font-bold">{{ msg.role === 'user' ? 'You' : 'DeepAgent' }}</span>
             <span v-if="msg.timestamp" class="font-mono">{{ formatTime(msg.timestamp) }}</span>
          </div>

          <!-- Bubble -->
          <div 
            class="p-4 rounded-2xl text-sm leading-7 shadow-sm break-words relative transition-all hover:shadow-md group"
            :class="[
              msg.role === 'user' 
                ? 'bg-indigo-600 text-white rounded-tr-none' 
                : 'bg-white border border-slate-200/60 text-slate-700 rounded-tl-none'
            ]"
          >
            <!-- Reasoning / Deep Thinking -->
            <div v-if="msg.reasoning" class="mb-3 bg-slate-50 rounded border border-slate-200 overflow-hidden">
              <div 
                class="flex items-center justify-between p-2 cursor-pointer hover:bg-slate-100 transition-colors select-none"
                @click="toggleReasoning(msg.id)"
              >
                <div class="flex items-center gap-2 text-slate-500 font-bold uppercase tracking-wider text-[10px]">
                  <span v-if="msg.streaming && !msg.content" class="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse"></span>
                  <span v-else class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                  Deep Thinking
                  <span class="opacity-50 font-normal normal-case ml-1">
                     {{ (msg.streaming && !msg.content) ? '(Thinking...)' : '(Completed)' }}
                  </span>
                </div>
                <Icon :name="isReasoningExpanded(msg.id) ? 'chevron-down' : 'chevron-right'" size="14" class="text-slate-400" />
              </div>
              
              <div v-show="isReasoningExpanded(msg.id)" class="px-3 pb-3 text-xs font-mono text-slate-500 whitespace-pre-wrap leading-relaxed border-t border-slate-200 pt-2 bg-white">
                {{ msg.reasoning }}
              </div>
            </div>

            <MarkdownRenderer v-if="msg.content" :content="msg.content" />
            <span v-if="msg.content && msg.streaming" class="inline-block w-1.5 h-4 ml-1 align-middle bg-indigo-400 animate-pulse"></span>
            
            <div v-if="!msg.content && msg.streaming" class="flex gap-1 h-6 items-center px-2">
              <div class="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style="animation-delay: 0ms"></div>
              <div class="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style="animation-delay: 150ms"></div>
              <div class="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style="animation-delay: 300ms"></div>
            </div>

            <!-- RAG Sources -->
            <div v-if="getRagSources(msg).length > 0" class="mt-4 pt-3 border-t border-slate-100">
               <div class="text-[10px] font-bold uppercase text-slate-400 mb-2 flex items-center gap-1">
                  <Icon name="book-open" size="12" />
                  References
               </div>
               <div class="space-y-1.5">
                  <div v-for="(source, idx) in getRagSources(msg)" :key="idx" 
                       class="flex items-start gap-2 text-xs bg-slate-50 p-2 rounded border border-slate-100 hover:border-indigo-200 hover:bg-indigo-50 transition-colors cursor-pointer"
                  >
                      <span class="text-indigo-500 font-mono text-[10px] shrink-0 mt-0.5">[{{ idx + 1 }}]</span>
                      <span class="text-slate-600 line-clamp-2">{{ source }}</span>
                  </div>
               </div>
            </div>

            <!-- Feedback Buttons (Assistant Only) -->
            <div v-if="msg.role === 'assistant' && !msg.streaming" class="absolute -bottom-3 right-4 opacity-0 group-hover:opacity-100 transition-opacity flex gap-1 bg-white shadow-sm border border-slate-200 rounded-full p-0.5">
                <button 
                    class="p-1 hover:bg-slate-100 rounded-full text-slate-400 hover:text-emerald-500 transition-colors" 
                    :class="{'text-emerald-500 bg-emerald-50': feedbackStatus[msg.id] === 'good'}"
                    title="Good response"
                    @click="submitFeedback(msg, 'good')"
                >
                    <Icon name="thumbs-up" size="12" />
                </button>
                <button 
                    class="p-1 hover:bg-slate-100 rounded-full text-slate-400 hover:text-rose-500 transition-colors" 
                    :class="{'text-rose-500 bg-rose-50': feedbackStatus[msg.id] === 'bad'}"
                    title="Bad response"
                    @click="submitFeedback(msg, 'bad')"
                >
                    <Icon name="thumbs-down" size="12" />
                </button>
            </div>
          </div>

          <!-- Tool Events (Thinking Process) -->
          <div v-if="msg.toolEvents && msg.toolEvents.length" class="w-full mt-2 border border-slate-200 rounded-lg overflow-hidden bg-white/50">
             <div class="bg-slate-50/80 px-3 py-2 border-b border-slate-200 flex items-center gap-2 text-[10px] font-bold uppercase text-slate-500 tracking-wider">
                <Icon name="cpu" size="12" />
                Work Process
             </div>
             <div class="p-2">
                <ToolEventCard 
                  v-for="evt in msg.toolEvents" 
                  :key="evt.id" 
                  :event="evt" 
                  @retry="$emit('retry-tool', evt)"
                  @debug="$emit('debug-tool', evt)"
                />
             </div>
          </div>
      </div>
    </div>
    
    <!-- Bottom Anchor -->
    <div ref="bottomAnchor" class="h-1"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, watch, onMounted, reactive } from 'vue'
import axios from 'axios'
import ToolEventCard from './ToolEventCard.vue'
import Icon from '../common/Icon.vue'
import MarkdownRenderer from '../common/MarkdownRenderer.vue'

const props = defineProps<{
  messages: Array<{
    id: string
    role: 'user' | 'assistant' | 'system'
    content: string
    reasoning?: string // Add reasoning prop type
    timestamp?: number
    streaming?: boolean
    toolEvents?: Array<any>
  }>
}>()

defineEmits<{
  (e: 'retry-tool', evt: any): void
  (e: 'debug-tool', evt: any): void
}>()

const container = ref<HTMLElement | null>(null)
const bottomAnchor = ref<HTMLElement | null>(null)
const shouldAutoScroll = ref(true)
const reasoningState = reactive<Record<string, boolean>>({})
const feedbackStatus = reactive<Record<string, 'good'|'bad'>>({})

async function submitFeedback(msg: any, rating: 'good' | 'bad') {
    // Optimistic UI update
    feedbackStatus[msg.id] = rating
    
    try {
        await axios.post('/api/v1/feedback', {
            id: msg.id,
            query: props.messages.find((m, i, arr) => arr[i+1]?.id === msg.id)?.content || '',
            response: msg.content,
            rating,
            timestamp: Date.now()
        })
    } catch (e) {
        console.error('Feedback failed', e)
        // Revert? Nah, keep it simple
    }
}

function toggleReasoning(id: string) {
  // Default is expanded (undefined -> true)
  // So if undefined, we want to collapse -> set to false
  if (reasoningState[id] === undefined) {
    reasoningState[id] = false
  } else {
    reasoningState[id] = !reasoningState[id]
  }
}

function isReasoningExpanded(id: string) {
  // Default to expanded
  return reasoningState[id] !== false
}

function getRagSources(msg: any) {
    if (!msg.toolEvents) return []
    const sources = new Set<string>()
    
    msg.toolEvents.forEach((evt: any) => {
        if (evt.name === 'search_knowledge_base' && evt.status === 'completed' && evt.output) {
            // Regex to find "Source: filename"
            const matches = evt.output.matchAll(/Source: (.+?)(?:\n|$)/g)
            for (const m of matches) {
                if (m[1]) sources.add(m[1].trim())
            }
        }
    })
    
    return Array.from(sources)
}

function onScroll() {
  if (!container.value) return
  const { scrollTop, scrollHeight, clientHeight } = container.value
  // User is considered "at bottom" if within 100px of the bottom
  shouldAutoScroll.value = scrollHeight - scrollTop - clientHeight < 100
}

function scrollToBottom(force = false) {
  if (!shouldAutoScroll.value && !force) return
  
  nextTick(() => {
    // Use 'auto' (instant) for streaming to avoid fighting user scrolling
    // Use 'smooth' only when forced (e.g. new message sent)
    bottomAnchor.value?.scrollIntoView({ behavior: force ? 'smooth' : 'auto', block: 'end' })
  })
}

// Watch for new messages
watch(() => props.messages.length, () => {
  // Always scroll to bottom for new user messages
  const lastMsg = props.messages[props.messages.length - 1]
  if (lastMsg?.role === 'user') {
    shouldAutoScroll.value = true
    scrollToBottom(true)
  } else {
    // For incoming assistant message start, we also want to ensure we are at bottom if we were before
    scrollToBottom()
  }
})

// Watch for content updates (streaming)
watch(() => props.messages[props.messages.length - 1]?.content, () => scrollToBottom())
watch(() => props.messages[props.messages.length - 1]?.reasoning, () => scrollToBottom())

onMounted(() => {
  scrollToBottom(true)
})

function formatTime(ts: number) {
  return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #334155;
  border-radius: 3px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #475569;
}
</style>