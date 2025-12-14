<template>
  <div class="flex flex-col gap-6 p-4 overflow-y-auto custom-scrollbar min-h-0" ref="container" @scroll="onScroll">
    <div v-for="msg in messages" :key="msg.id" 
      class="flex flex-col gap-1 w-full transition-all duration-300"
      :class="msg.role === 'user' ? 'items-end' : 'items-start'"
    >
      <!-- Avatar/Role -->
      <div class="flex items-center gap-2 px-3 opacity-70 text-xs">
        <span v-if="msg.role === 'assistant'" class="w-2 h-2 rounded-full bg-accent"></span>
        <span v-if="msg.role === 'user'" class="w-2 h-2 rounded-full bg-slate-400"></span>
        <span>{{ msg.role === 'user' ? 'User' : 'DeepAgent' }}</span>
        <span class="text-[10px] font-mono" v-if="msg.timestamp">{{ formatTime(msg.timestamp) }}</span>
      </div>
      
      <!-- Content Bubble -->
      <div 
        class="p-4 rounded-2xl text-sm leading-7 shadow-sm max-w-[90%] md:max-w-[80%] transition-all duration-200 hover:shadow-md break-words"
        :class="[
          msg.role === 'user' 
            ? 'bg-[#7c3aed]/10 border border-[#7c3aed]/30 text-white rounded-tr-sm hover:bg-[#7c3aed]/15' 
            : 'bg-[#1e293b]/50 border border-slate-700/50 text-slate-200 rounded-tl-sm backdrop-blur-sm hover:bg-[#1e293b]/70'
        ]"
      >
        <!-- Reasoning / Deep Thinking -->
        <div v-if="msg.reasoning" class="mb-3 bg-black/20 rounded border border-white/5 overflow-hidden">
          <div 
            class="flex items-center justify-between p-3 cursor-pointer hover:bg-white/5 transition-colors select-none"
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
            <Icon :name="isReasoningExpanded(msg.id) ? 'chevron-down' : 'chevron-right'" size="14" class="text-slate-500" />
          </div>
          
          <div v-show="isReasoningExpanded(msg.id)" class="px-3 pb-3 text-xs font-mono text-slate-400 whitespace-pre-wrap leading-relaxed border-t border-white/5 pt-2">
            {{ msg.reasoning }}
          </div>
        </div>

        <MarkdownRenderer v-if="msg.content" :content="msg.content" />
        <span v-if="msg.content && msg.streaming" class="inline-block w-1.5 h-4 ml-1 align-middle bg-accent animate-pulse"></span>
        
        <div v-if="!msg.content && msg.streaming" class="flex gap-1 h-6 items-center">
          <div class="w-2 h-2 bg-accent rounded-full animate-bounce" style="animation-delay: 0ms"></div>
          <div class="w-2 h-2 bg-accent rounded-full animate-bounce" style="animation-delay: 150ms"></div>
          <div class="w-2 h-2 bg-accent rounded-full animate-bounce" style="animation-delay: 300ms"></div>
        </div>
      </div>

      <!-- Tool Events -->
      <div v-if="msg.toolEvents && msg.toolEvents.length" class="w-full max-w-[90%] md:max-w-[80%] pl-2 border-l-2 border-slate-800 ml-2 mt-1">
        <ToolEventCard 
          v-for="evt in msg.toolEvents" 
          :key="evt.id" 
          :event="evt" 
          @retry="$emit('retry-tool', evt)"
          @debug="$emit('debug-tool', evt)"
        />
      </div>
    </div>
    
    <!-- Bottom Anchor -->
    <div ref="bottomAnchor" class="h-1"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, watch, onMounted, reactive } from 'vue'
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