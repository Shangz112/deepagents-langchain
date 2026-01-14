<template>
  <div class="grid gap-3 p-4 bg-[#0f172a] border-t border-slate-700">
    <!-- Toolbar -->
    <div class="flex items-center gap-3 overflow-x-auto pb-1 no-scrollbar">
      <button 
        class="btn p-1.5 text-xs flex items-center gap-1 transition-colors" 
        @click="setMode('fast')" 
        :class="mode === 'fast' ? 'border-emerald-500 text-emerald-500 bg-emerald-500/10' : 'text-slate-400 hover:text-slate-200'"
      >
        <span class="text-lg">⚡</span> 快速对话
      </button>
      <button 
        class="btn p-1.5 text-xs flex items-center gap-1 transition-colors" 
        @click="setMode('agent')" 
        :class="mode === 'agent' ? 'border-accent text-accent bg-accent/10' : 'text-slate-400 hover:text-slate-200'"
      >
        <span class="text-lg">🛠️</span> 深度代理
      </button>
      <div class="w-px h-4 bg-slate-700 mx-1"></div>
      <button class="btn p-1.5 text-xs flex items-center gap-1" @click="toggleTemplate" :class="{ 'border-accent text-accent': showTemplates }">
        <span class="text-lg">📋</span> 模板
      </button>
      <button class="btn p-1.5 text-xs flex items-center gap-1" @click="triggerUpload">
        <span class="text-lg">📎</span> 附件
        <input type="file" ref="fileInput" class="hidden" @change="handleFile" />
      </button>
      <div class="flex-1"></div>
      <select v-model="selectedPreset" class="bg-transparent border border-slate-700 rounded px-2 py-1 text-xs text-slate-400 outline-none focus:border-accent">
        <option value="default">默认预设</option>
        <option value="creative">创意模式</option>
        <option value="precise">精确模式</option>
      </select>
    </div>

    <!-- Template Selector -->
    <div v-if="showTemplates" class="grid gap-2 p-3 bg-[#0b0f14] rounded-lg border border-slate-700 animate-in slide-in-from-bottom-2">
      <div class="flex justify-between items-center">
        <span class="text-xs font-bold text-slate-400">选择模板</span>
        <button class="text-slate-500 hover:text-white" @click="showTemplates = false">✕</button>
      </div>
      <div class="flex gap-2 overflow-x-auto pb-2">
        <button 
          v-for="t in templates" 
          :key="t.id" 
          class="shrink-0 px-3 py-2 rounded border border-slate-700 hover:border-accent text-xs text-left w-32 truncate transition-colors"
          @click="applyTemplate(t)"
        >
          {{ t.name }}
        </button>
      </div>
      <!-- Variable Interpolation -->
      <div v-if="currentTemplate" class="grid gap-2 mt-2 border-t border-slate-800 pt-2">
        <div v-for="v in currentTemplate.vars" :key="v" class="grid grid-cols-[60px_1fr] gap-2 items-center">
          <label class="text-xs text-slate-500 text-right">{{ v }}:</label>
          <input v-model="templateVars[v]" class="input text-xs py-1" :placeholder="v" />
        </div>
      </div>
    </div>

    <!-- Input Area -->
    <div class="relative">
      <textarea 
        v-model="text" 
        rows="3" 
        class="w-full bg-[#0b0f14] border border-slate-700 rounded-lg p-3 text-sm focus:border-accent focus:ring-1 focus:ring-accent outline-none resize-none custom-scrollbar transition-all" 
        :placeholder="placeholder"
        @keydown.enter.exact.prevent="send"
        @keydown.ctrl.enter="send"
      />
      <div class="absolute bottom-2 right-2 flex items-center gap-2">
        <span class="text-[10px] text-slate-600 hidden md:inline">Ctrl + Enter 发送</span>
        <button 
          class="btn btn-accent p-2 rounded-full w-8 h-8 flex items-center justify-center shadow-lg hover:shadow-accent/20" 
          @click="send"
          :disabled="!canSend"
        >
          ➤
        </button>
      </div>
    </div>

    <!-- File Preview -->
    <div v-if="files.length" class="flex gap-2 flex-wrap">
      <div v-for="(f, i) in files" :key="i" class="pill text-xs bg-slate-800 border-slate-600">
        {{ f.name }}
        <button class="ml-1 text-slate-400 hover:text-red-400" @click="files.splice(i, 1)">×</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

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

const canSend = computed(() => text.value.trim().length > 0 || files.value.length > 0)

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