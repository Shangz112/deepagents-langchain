<template>
  <div class="h-full grid grid-cols-1 md:grid-cols-[320px_1fr] gap-0 bg-[var(--bg-app)]">
    <!-- Template List (Sidebar) -->
    <div class="flex flex-col border-r border-[var(--border-subtle)] bg-[var(--bg-panel)]">
      <div class="p-4 border-b border-[var(--border-subtle)] flex justify-between items-center h-[56px]">
        <span class="font-semibold text-[var(--fg-primary)] flex items-center gap-2">
          <Icon name="book-open" size="18" class="text-[var(--accent-primary)]" />
          Prompt Templates
        </span>
        <button class="btn btn-sm btn-secondary gap-1.5" @click="createNew">
          <Icon name="plus" size="14" />
          New
        </button>
      </div>
      
      <div class="flex-1 overflow-y-auto p-3 space-y-2">
        <div v-for="t in templates" :key="t.id" 
             class="p-3 rounded-lg border transition-all cursor-pointer group relative"
             :class="selectedId === t.id ? 'bg-[var(--accent-surface)] border-[var(--accent-primary)]/50 shadow-sm' : 'bg-[var(--bg-surface)] border-[var(--border-subtle)] hover:border-[var(--border-active)]'"
             @click="selectTemplate(t)">
          
          <div class="flex justify-between items-start mb-1">
            <div class="font-medium text-sm" :class="selectedId === t.id ? 'text-[var(--accent-primary)]' : 'text-[var(--fg-primary)]'">{{ t.name }}</div>
            <div v-if="selectedId === t.id" class="h-2 w-2 rounded-full bg-[var(--accent-primary)]"></div>
          </div>
          
          <div class="text-xs text-[var(--fg-secondary)] mt-1 line-clamp-2 leading-relaxed">{{ t.desc }}</div>
          
          <div class="flex items-center justify-between mt-3 pt-2 border-t border-[var(--border-subtle)]/50" :class="selectedId === t.id ? 'border-[var(--accent-primary)]/20' : ''">
            <span class="text-[10px] font-mono text-[var(--fg-tertiary)] bg-[var(--bg-app)] px-1.5 py-0.5 rounded">v{{ t.version }}</span>
            <span class="text-[10px] text-[var(--fg-tertiary)]">{{ t.updated }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Editor & Preview -->
    <div class="flex flex-col h-full overflow-hidden relative">
      <!-- Toolbar -->
      <div class="h-[56px] border-b border-[var(--border-subtle)] bg-[var(--bg-panel)]/50 backdrop-blur-sm flex justify-between items-center px-6">
        <div class="flex items-center gap-3 flex-1 mr-4">
          <input v-model="name" class="font-bold text-[var(--fg-primary)] bg-transparent border-none outline-none w-full placeholder-[var(--fg-tertiary)]" placeholder="Enter template name..." />
          <span class="text-xs px-2 py-0.5 rounded-full bg-[var(--accent-surface)] text-[var(--accent-primary)] border border-[var(--accent-primary)]/20 whitespace-nowrap">Edited</span>
        </div>
        <div class="flex gap-3">
          <button class="btn btn-sm btn-ghost gap-2">
            <Icon name="refresh-cw" size="14" />
            History
          </button>
          <button class="btn btn-sm btn-primary gap-2" @click="save">
            <Icon name="save" size="14" />
            Save Changes
          </button>
        </div>
      </div>
      
      <!-- Editor Area -->
      <div class="flex-1 p-6 overflow-hidden flex flex-col gap-6">
        <!-- Main Input -->
        <div class="flex-1 relative group">
          <div class="absolute inset-0 bg-gradient-to-b from-[var(--accent-primary)]/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none rounded-xl"></div>
          <textarea 
            v-model="content" 
            class="w-full h-full bg-[var(--bg-surface)] p-6 rounded-xl border border-[var(--border-subtle)] font-mono text-sm text-[var(--fg-primary)] focus:border-[var(--accent-primary)] focus:ring-1 focus:ring-[var(--accent-primary)] outline-none resize-none leading-relaxed transition-all shadow-sm"
            placeholder="Enter prompt template using {{variable}} syntax..."
          ></textarea>
        </div>
        
        <!-- Variable Configuration -->
        <div class="h-[180px] shrink-0 bg-[var(--bg-panel)] rounded-xl border border-[var(--border-subtle)] flex flex-col overflow-hidden shadow-lg">
          <div class="px-4 py-2 bg-[var(--bg-surface)] border-b border-[var(--border-subtle)] flex items-center justify-between">
             <div class="text-xs font-bold text-[var(--fg-secondary)] uppercase tracking-wider flex items-center gap-2">
               <Icon name="cpu" size="14" />
               Variables & Test
             </div>
             <span class="text-[10px] text-[var(--fg-tertiary)]">{{ extractedVars.length }} detected</span>
          </div>
          
          <div class="p-4 overflow-y-auto">
            <div v-if="extractedVars.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div v-for="v in extractedVars" :key="v" class="group flex items-center gap-3 bg-[var(--bg-app)] p-2 rounded-lg border border-[var(--border-subtle)] focus-within:border-[var(--accent-primary)] transition-colors">
                <span class="text-xs font-mono text-[var(--accent-primary)] bg-[var(--accent-surface)] px-2 py-1 rounded shrink-0">{{ v }}</span>
                <input 
                  class="bg-transparent text-sm text-[var(--fg-primary)] w-full outline-none placeholder-[var(--fg-tertiary)]" 
                  :placeholder="'Value for ' + v" 
                />
              </div>
            </div>
            <div v-else class="flex flex-col items-center justify-center h-full text-[var(--fg-tertiary)] gap-2 opacity-60">
              <Icon name="code" size="24" />
              <span class="text-sm" v-pre>Use {{ variable }} syntax to define dynamic slots</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import Icon from '../components/common/Icon.vue'
import { promptStore } from '../store'

const selectedId = ref<string | null>(null)
const content = ref('')
const name = ref('')
const desc = ref('')

onMounted(async () => {
  await promptStore.loadPrompts()
  if (promptStore.prompts.length > 0) {
    selectTemplate(promptStore.prompts[0])
  }
})

function selectTemplate(t: any) {
  selectedId.value = t.id
  content.value = t.content || ''
  name.value = t.name
  desc.value = t.desc
}

function createNew() {
  selectedId.value = null
  content.value = ''
  name.value = 'New Prompt'
  desc.value = 'Description here...'
}

async function save() {
  const p = {
    id: selectedId.value,
    name: name.value,
    desc: desc.value,
    content: content.value,
    version: '1.0'
  }
  const newId = await promptStore.savePrompt(p)
  selectedId.value = newId
}

const templates = computed(() => promptStore.prompts)
const selectedTemplate = computed(() => templates.value.find((t: any) => t.id === selectedId.value))

const extractedVars = computed(() => {
  const matches = content.value.match(/{{([^}]+)}}/g)
  if (!matches) return []
  return Array.from(new Set(matches.map(m => m.slice(2, -2).trim())))
})
</script>

<style scoped>
/* Custom Scrollbar for this component */
textarea::-webkit-scrollbar {
  width: 8px;
}
textarea::-webkit-scrollbar-track {
  background: transparent;
}
textarea::-webkit-scrollbar-thumb {
  background: var(--border-subtle);
  border-radius: 4px;
}
textarea::-webkit-scrollbar-thumb:hover {
  background: var(--fg-tertiary);
}
</style>
