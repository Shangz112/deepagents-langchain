<template>
  <div class="grid gap-3 p-4 bg-[var(--bg-panel)] border-t border-[var(--border-subtle)]">
    <!-- Toolbar -->
    <div class="flex items-center gap-3 overflow-x-auto pb-1 no-scrollbar">
      <button 
        class="btn p-1.5 text-xs flex items-center gap-1 transition-colors" 
        @click="setMode('fast')" 
        :class="mode === 'fast' ? 'border-emerald-500 text-emerald-500 bg-emerald-500/10' : 'text-[var(--fg-tertiary)] hover:text-[var(--fg-secondary)]'"
      >
        <span class="text-lg">⚡</span> 快速对话
      </button>
      <button 
        class="btn p-1.5 text-xs flex items-center gap-1 transition-colors" 
        @click="setMode('agent')" 
        :class="mode === 'agent' ? 'border-[var(--accent-primary)] text-[var(--accent-primary)] bg-[var(--accent-surface)]/10' : 'text-[var(--fg-tertiary)] hover:text-[var(--fg-secondary)]'"
      >
        <span class="text-lg">🛠️</span> 深度代理
      </button>
      <div class="w-px h-4 bg-[var(--border-subtle)] mx-1"></div>
      <button class="btn p-1.5 text-xs flex items-center gap-1 text-[var(--fg-tertiary)] hover:text-[var(--fg-primary)]" @click="toggleTemplate" :class="{ 'border-[var(--accent-primary)] text-[var(--accent-primary)]': showTemplates }">
        <span class="text-lg">📋</span> 模板
      </button>
      <button class="btn p-1.5 text-xs flex items-center gap-1 text-[var(--fg-tertiary)] hover:text-[var(--fg-primary)]" @click="triggerUpload">
        <span class="text-lg">📎</span> 附件
        <input type="file" ref="fileInput" class="hidden" @change="handleFile" />
      </button>
      <div class="flex-1"></div>
      <select v-model="selectedPreset" class="bg-transparent border border-[var(--border-subtle)] rounded px-2 py-1 text-xs text-[var(--fg-tertiary)] outline-none focus:border-[var(--accent-primary)]">
        <option value="default">默认预设</option>
        <option value="creative">创意模式</option>
        <option value="precise">精确模式</option>
      </select>
    </div>

    <!-- Template Selector -->
    <div v-if="showTemplates" class="grid gap-2 p-3 bg-[var(--bg-app)] rounded-lg border border-[var(--border-subtle)] animate-in slide-in-from-bottom-2">
      <div class="flex justify-between items-center">
        <span class="text-xs font-bold text-[var(--fg-tertiary)]">选择模板</span>
        <button class="text-[var(--fg-tertiary)] hover:text-[var(--fg-primary)]" @click="showTemplates = false">✕</button>
      </div>
      <div class="flex gap-2 overflow-x-auto pb-2">
        <button 
          v-for="t in templates" 
          :key="t.id" 
          class="shrink-0 px-3 py-2 rounded border border-[var(--border-subtle)] hover:border-[var(--accent-primary)] text-xs text-left w-32 truncate transition-colors text-[var(--fg-secondary)]"
          @click="applyTemplate(t)"
        >
          {{ t.name }}
        </button>
      </div>
      <!-- Variable Interpolation -->
      <div v-if="currentTemplate" class="grid gap-2 mt-2 border-t border-[var(--border-subtle)] pt-2">
        <div v-for="v in currentTemplate.vars" :key="v" class="grid grid-cols-[60px_1fr] gap-2 items-center">
          <label class="text-xs text-[var(--fg-tertiary)] text-right">{{ v }}:</label>
          <input v-model="templateVars[v]" class="input text-xs py-1 bg-[var(--bg-surface)] border-[var(--border-subtle)] text-[var(--fg-primary)]" :placeholder="v" />
        </div>
      </div>
    </div>

    <!-- Input Area -->
    <div class="relative">
      <textarea 
        v-model="text" 
        rows="3" 
        class="w-full bg-[var(--bg-app)] border border-[var(--border-subtle)] rounded-lg p-3 text-sm text-[var(--fg-primary)] focus:border-[var(--accent-primary)] focus:ring-1 focus:ring-[var(--accent-primary)] outline-none resize-none custom-scrollbar transition-all placeholder-[var(--fg-tertiary)]" 
        :placeholder="placeholder"
        @keydown.enter.exact.prevent="send"
        @keydown.ctrl.enter="send"
      />
      <div class="absolute bottom-2 right-2 flex items-center gap-2">
        <span class="text-[10px] text-[var(--fg-tertiary)] hidden md:inline">Ctrl + Enter 发送</span>
        <button 
          class="btn p-2 rounded-full w-8 h-8 flex items-center justify-center shadow-lg transition-all duration-300"
          :class="[
            chatStore.isStreaming 
              ? 'bg-red-500 hover:bg-red-600 text-white shadow-red-500/20' 
              : 'bg-[var(--accent-primary)] hover:bg-[var(--accent-hover)] text-white shadow-[var(--accent-glow)]',
            !canSend && !chatStore.isStreaming ? 'opacity-50 cursor-not-allowed' : ''
          ]" 
          @click="handleClick"
          :disabled="!canSend && !chatStore.isStreaming"
        >
          <span v-if="chatStore.isStreaming" class="text-sm font-bold">■</span>
          <span v-else>➤</span>
        </button>
      </div>
    </div>

    <!-- File Preview -->
    <div v-if="files.length" class="flex gap-2 flex-wrap">
      <div v-for="(f, i) in files" :key="i" class="pill text-xs bg-[var(--bg-surface)] border-[var(--border-subtle)] text-[var(--fg-secondary)]">
        {{ f.name }}
        <button class="ml-1 text-[var(--fg-tertiary)] hover:text-red-400" @click="files.splice(i, 1)">×</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { chatStore } from '../../store'

const emit = defineEmits<{ 
  (e: 'send', payload: { text: string; tools: boolean; template?: any; files: File[] }): void 
}>()

const text = ref('')
const mode = ref<'fast' | 'agent'>('fast')
const showTemplates = ref(false)
const selectedPreset = ref('default')
const files = ref<File[]>([])
const fileInput = ref<HTMLInputElement | null>(null)

// Templates
const templates = ref<any[]>([])

onMounted(async () => {
  try {
    const r = await axios.get('/api/v1/prompts/templates')
    // Filter or map if necessary. Assuming backend returns list of prompts with 'content' and 'name'
    // We might need to parse 'content' to find {{vars}} if the backend doesn't provide them.
    // For now, let's use the fetched prompts.
    templates.value = r.data.map((p: any) => ({
      id: p.id,
      name: p.name,
      content: p.content,
      vars: extractVars(p.content)
    }))
  } catch (e) {
    console.error('Failed to load prompts', e)
    templates.value = []
  }
})

function extractVars(content: string): string[] {
  const regex = /{{(.*?)}}/g
  const vars = []
  let match
  while ((match = regex.exec(content)) !== null) {
    vars.push(match[1].trim())
  }
  return [...new Set(vars)] // Unique
}

const currentTemplate = ref<any>(null)
const templateVars = ref<Record<string, string>>({})

function setMode(m: 'fast' | 'agent') { mode.value = m }
function toggleTemplate() { showTemplates.value = !showTemplates.value }

function triggerUpload() { fileInput.value?.click() }
function handleFile(e: Event) {
  const target = e.target as HTMLInputElement
  if (target.files?.length) {
    files.value.push(...Array.from(target.files))
  }
}

function applyTemplate(t: any) {
  currentTemplate.value = t
  templateVars.value = {}
  t.vars.forEach((v: string) => templateVars.value[v] = '')
  // We don't set text immediately, we let user fill vars first or just use the template structure
  text.value = t.content
}

const placeholder = computed(() => {
  if (currentTemplate.value) return '填写变量或编辑模板内容...'
  return '输入消息，支持 Markdown...'
})

const canSend = computed(() => (text.value.trim().length > 0 || files.value.length > 0) && !chatStore.isStreaming)

async function handleClick() {
  if (chatStore.isStreaming) {
    await chatStore.abortGeneration()
  } else {
    send()
  }
}

function send() {
  if (!canSend.value) return
  
  // Process template vars if needed
  let finalText = text.value
  if (currentTemplate.value) {
    Object.entries(templateVars.value).forEach(([k, v]) => {
      finalText = finalText.replace(new RegExp(`{{${k}}}`, 'g'), v)
    })
  }

  emit('send', { 
    text: finalText, 
    tools: mode.value === 'agent', 
    template: currentTemplate.value ? { id: currentTemplate.value.id, vars: templateVars.value } : undefined,
    files: files.value 
  })
  
  text.value = ''
  files.value = []
  showTemplates.value = false
  currentTemplate.value = null
}
</script>

<style scoped>
.no-scrollbar::-webkit-scrollbar { display: none; }
</style>