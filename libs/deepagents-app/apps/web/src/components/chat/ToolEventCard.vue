<template>
  <div class="panel border border-slate-700 rounded-lg p-3 my-2 text-sm relative group">
    <div class="flex items-center justify-between cursor-pointer" @click="expanded = !expanded">
      <div class="flex items-center gap-2">
        <span class="text-xs font-mono text-slate-500">TOOL</span>
        <span class="font-bold text-accent">{{ event.name }}</span>
        <span class="text-xs px-2 py-0.5 rounded" :class="statusClass">{{ event.status }}</span>
      </div>
      <div class="flex items-center gap-2 text-xs text-slate-500">
        <span v-if="event.duration">{{ event.duration }}ms</span>
        <span :class="expanded ? 'rotate-180' : ''" class="transition-transform">▼</span>
      </div>
    </div>
    
    <!-- Summary View -->
    <div v-if="!expanded" class="mt-2 text-slate-400 truncate">
      {{ summary }}
    </div>

    <!-- Expanded Details -->
    <div v-if="expanded" class="mt-3 border-t border-slate-700 pt-3 grid gap-3">
      <!-- Input -->
      <div>
        <div class="text-xs uppercase tracking-wider text-slate-500 mb-1 flex justify-between">
          <span>Input</span>
          <button class="hover:text-white" @click.stop="copy(event.input)">Copy</button>
        </div>
        <pre class="bg-[#0b0f14] p-2 rounded text-xs text-slate-300 overflow-x-auto whitespace-pre-wrap break-all">{{ formatData(event.input) }}</pre>
      </div>

      <!-- Output -->
      <div v-if="event.output">
        <div class="text-xs uppercase tracking-wider text-slate-500 mb-1 flex justify-between">
          <span>Output</span>
          <button class="hover:text-white" @click.stop="copy(event.output)">Copy</button>
        </div>
        <pre class="bg-[#0b0f14] p-2 rounded text-xs text-slate-300 overflow-x-auto max-h-60 whitespace-pre-wrap break-all">{{ formatData(event.output) }}</pre>
      </div>

      <!-- Actions -->
      <div class="flex gap-2 justify-end border-t border-slate-800 pt-2">
        <button class="btn text-xs py-1" @click.stop="$emit('retry', event)">Retry</button>
        <button class="btn text-xs py-1" @click.stop="$emit('debug', event)">Debug</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps<{
  event: {
    id: string
    name: string
    status: 'pending' | 'success' | 'failed' | 'retrying'
    input: any
    output?: any
    duration?: number
    error?: string
  }
}>()

const emit = defineEmits<{
  (e: 'retry', event: any): void
  (e: 'debug', event: any): void
}>()

const expanded = ref(false)

const statusClass = computed(() => {
  switch (props.event.status) {
    case 'success': return 'bg-emerald-500/20 text-emerald-400'
    case 'failed': return 'bg-red-500/20 text-red-400'
    case 'pending': return 'bg-blue-500/20 text-blue-400 animate-pulse'
    default: return 'bg-slate-700 text-slate-300'
  }
})

const summary = computed(() => {
  if (props.event.output) {
    const s = typeof props.event.output === 'string' ? props.event.output : JSON.stringify(props.event.output)
    return 'Result: ' + s
  }
  return 'Input: ' + JSON.stringify(props.event.input)
})

function copy(data: any) {
  navigator.clipboard.writeText(typeof data === 'string' ? data : JSON.stringify(data, null, 2))
}

function formatData(data: any) {
  if (typeof data === 'string') return data
  return JSON.stringify(data, null, 2)
}
</script>

<style scoped>
.text-accent { color: var(--accent); }
</style>