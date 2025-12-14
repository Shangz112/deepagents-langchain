<template>
  <div class="h-full flex flex-col overflow-hidden bg-[var(--bg-app)]">
    <!-- Header -->
    <header class="flex-none p-6 border-b border-[var(--border-subtle)] bg-[var(--bg-panel)]/80 backdrop-blur-md">
      <div class="flex justify-between items-center">
        <div>
          <h1 class="text-2xl font-bold text-[var(--fg-primary)] tracking-tight flex items-center gap-3">
            <Icon name="database" size="28" class="text-[var(--accent-primary)]" />
            Knowledge Base
          </h1>
          <p class="text-[var(--fg-secondary)] text-sm mt-1">Manage data sources and test retrieval pipelines</p>
        </div>
        <button @click="showAddModal = true" class="btn btn-primary gap-2">
          <Icon name="plus" size="16" />
          Add Source
        </button>
      </div>
    </header>

    <div class="flex-1 flex overflow-hidden">
      <!-- Sidebar: Sources List -->
      <aside class="w-80 border-r border-[var(--border-subtle)] bg-[var(--bg-panel)]/30 flex flex-col">
        <div class="p-4 border-b border-[var(--border-subtle)]">
           <div class="relative">
             <Icon name="search" size="14" class="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--fg-tertiary)]" />
             <input v-model="sourceFilter" type="text" class="w-full bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-lg pl-9 pr-3 py-2 text-sm text-[var(--fg-primary)] focus:border-[var(--accent-primary)] outline-none transition-all" placeholder="Filter sources..." />
           </div>
        </div>
        <div class="flex-1 overflow-y-auto p-2 space-y-2">
          <div v-for="source in filteredSources" :key="source.id" 
               class="p-3 rounded-lg border border-transparent hover:bg-[var(--bg-surface)] cursor-pointer transition-all group"
               :class="{ 'bg-[var(--bg-surface)] border-[var(--border-subtle)] shadow-sm': selectedSource?.id === source.id }">
            <div class="flex justify-between items-start mb-1">
              <div class="font-medium text-[var(--fg-primary)] truncate">{{ source.name }}</div>
              <span class="text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded bg-[var(--bg-app)] border border-[var(--border-subtle)] text-[var(--fg-tertiary)]">{{ source.type }}</span>
            </div>
            <div class="text-xs text-[var(--fg-secondary)] flex items-center gap-2 mt-2">
              <span class="flex h-2 w-2 rounded-full" :class="source.status === 'ready' ? 'bg-[var(--success)]' : 'bg-[var(--warning)]'"></span>
              {{ source.status }}
              <span class="ml-auto text-[var(--fg-tertiary)]">{{ source.docCount }} docs</span>
            </div>
          </div>
        </div>
      </aside>

      <!-- Main Content: Retrieval Testing -->
      <main class="flex-1 flex flex-col overflow-hidden bg-[var(--bg-app)] relative">
        <!-- Background Pattern -->
        <div class="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAiIGhlaWdodD0iMjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGNpcmNsZSBjeD0iMSIgY3k9IjEiIHI9IjEiIGZpbGw9InJnYmEoMjU1LDI1NSwyNTUsMC4wNSkiLz48L3N2Zz4=')] opacity-20 pointer-events-none"></div>

        <div class="p-8 flex-none z-10">
          <div class="max-w-3xl mx-auto w-full">
             <div class="relative group">
               <div class="absolute -inset-1 bg-gradient-to-r from-[var(--accent-primary)] to-[var(--accent-hover)] rounded-xl opacity-20 blur group-hover:opacity-40 transition duration-1000 group-hover:duration-200"></div>
               <div class="relative flex items-center">
                 <input v-model="query" @keyup.enter="search" type="text" class="w-full bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl px-5 py-4 pl-12 text-lg text-[var(--fg-primary)] focus:border-[var(--accent-primary)] outline-none shadow-lg transition-all placeholder-[var(--fg-tertiary)]" placeholder="Ask your knowledge base..." />
                 <Icon name="search" size="20" class="absolute left-4 text-[var(--fg-tertiary)]" />
                 <button @click="search" class="absolute right-3 btn btn-sm btn-primary px-4">Search</button>
               </div>
             </div>
          </div>
        </div>

        <div class="flex-1 overflow-y-auto px-6 pb-6 z-10">
          <div class="max-w-3xl mx-auto w-full space-y-4">
            <div v-if="loading" class="text-center py-12 text-[var(--fg-tertiary)] flex flex-col items-center">
              <Icon name="refresh-cw" size="32" class="animate-spin mb-4 text-[var(--accent-primary)]" />
              Searching vector store...
            </div>

            <div v-else-if="records.length > 0" class="space-y-4">
              <div v-for="record in records" :key="record.id" class="panel-card p-5 hover:border-[var(--accent-primary)]/50 transition-all group">
                <div class="flex justify-between items-start mb-3">
                   <div class="flex items-center gap-3">
                      <span class="text-xs font-bold font-mono text-[var(--accent-primary)] bg-[var(--accent-surface)] px-2 py-1 rounded border border-[var(--accent-primary)]/20">{{ (record.score * 100).toFixed(1) }}% Match</span>
                      <span class="text-xs text-[var(--fg-secondary)] flex items-center gap-1">
                        <Icon name="file-text" size="12" /> <!-- Need file-text, fallback to generic -->
                        {{ record.source }}
                      </span>
                   </div>
                   <button class="text-[var(--fg-tertiary)] hover:text-[var(--fg-primary)] opacity-0 group-hover:opacity-100 transition-opacity">
                     <Icon name="maximize" size="14" />
                   </button>
                </div>
                <p class="text-[var(--fg-secondary)] text-sm leading-relaxed" v-html="highlightMatch(record.content)"></p>
              </div>
            </div>
             <div v-else-if="hasSearched" class="text-center py-12 text-[var(--fg-tertiary)]">
              No relevant documents found.
            </div>
             <div v-else class="text-center py-20 text-[var(--fg-tertiary)] flex flex-col items-center opacity-50">
               <Icon name="book-open" size="48" class="mb-4" />
               <p>Enter a query above to test semantic search retrieval.</p>
            </div>
          </div>
        </div>
      </main>
    </div>

    <!-- Add Source Modal -->
    <div v-if="showAddModal" class="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center">
      <div class="w-full max-w-md p-6 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-panel)] shadow-2xl relative overflow-hidden">
        <!-- Glow effect -->
        <div class="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-[var(--accent-primary)] to-transparent"></div>
        
        <h3 class="text-xl font-bold text-[var(--fg-primary)] mb-6 flex items-center gap-2">
          <Icon name="plus" size="20" />
          Add Knowledge Source
        </h3>
        
        <div class="space-y-5">
          <div>
            <label class="block text-xs font-bold text-[var(--fg-secondary)] uppercase tracking-wider mb-1.5">Source Name</label>
            <input v-model="newSource.name" class="input" placeholder="e.g. Engineering Docs" />
          </div>
           <div>
            <label class="block text-xs font-bold text-[var(--fg-secondary)] uppercase tracking-wider mb-1.5">Type</label>
            <div class="grid grid-cols-3 gap-2">
              <button v-for="t in ['folder', 'github', 'web']" :key="t"
                class="flex flex-col items-center gap-1 p-3 rounded-lg border transition-all"
                :class="newSource.type === t ? 'bg-[var(--accent-surface)] border-[var(--accent-primary)] text-[var(--accent-primary)]' : 'bg-[var(--bg-surface)] border-[var(--border-subtle)] text-[var(--fg-secondary)] hover:border-[var(--fg-tertiary)]'"
                @click="newSource.type = t as any"
              >
                <Icon :name="getSourceIcon(t)" size="18" />
                <span class="text-xs capitalize">{{ t }}</span>
              </button>
            </div>
          </div>
           <div>
            <label class="block text-xs font-bold text-[var(--fg-secondary)] uppercase tracking-wider mb-1.5">Path / URL</label>
            <input v-model="newSource.path" class="input" placeholder="https://..." />
          </div>
        </div>
        
        <div class="flex justify-end gap-3 mt-8">
          <button @click="showAddModal = false" class="btn btn-ghost">Cancel</button>
          <button @click="addSource" class="btn btn-primary">Add Source</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive } from 'vue'
import axios from 'axios'
import Icon from '../components/common/Icon.vue'

interface Source {
  id: string;
  name: string;
  type: 'folder' | 'github' | 'web';
  status: 'ready' | 'indexing' | 'error';
  docCount: number;
}

interface Record {
  id: string;
  content: string;
  source: string;
  score: number;
}

const query = ref('')
const loading = ref(false)
const hasSearched = ref(false)
const showAddModal = ref(false)
const sourceFilter = ref('')
const selectedSource = ref<Source | null>(null)

const newSource = reactive({
  name: '',
  type: 'folder',
  path: ''
})

// Mock Sources
const sources = ref<Source[]>([
  { id: '1', name: 'Project Documentation', type: 'folder', status: 'ready', docCount: 142 },
  { id: '2', name: 'LangChain API Ref', type: 'web', status: 'indexing', docCount: 45 },
  { id: '3', name: 'Team Wiki', type: 'github', status: 'ready', docCount: 89 }
])

const filteredSources = computed(() => {
  if (!sourceFilter.value) return sources.value
  return sources.value.filter(s => s.name.toLowerCase().includes(sourceFilter.value.toLowerCase()))
})

const records = ref<Record[]>([])

const search = async () => {
  if (!query.value) return
  loading.value = true
  hasSearched.value = true
  
  // Mock delay
  await new Promise(r => setTimeout(r, 800))
  
  try {
    // Try real API
    const r = await axios.get('/api/v1/kb/query', { params: { q: query.value } })
    records.value = r.data.records || []
  } catch (e) {
    // Fallback Mock Results
    records.value = [
      { id: '1', content: 'The memory system consists of short-term memory (context window) and long-term memory (vector database).', source: 'Project Documentation/Architecture.md', score: 0.92 },
      { id: '2', content: 'Vector stores allow for semantic search by embedding text into high-dimensional vectors.', source: 'LangChain API Ref/VectorStores', score: 0.85 },
      { id: '3', content: 'To configure the memory backend, edit the config.yaml file in the root directory.', source: 'Team Wiki/Setup', score: 0.78 }
    ]
  } finally {
    loading.value = false
  }
}

const addSource = () => {
  sources.value.push({
    id: String(Date.now()),
    name: newSource.name,
    type: newSource.type as any,
    status: 'indexing',
    docCount: 0
  })
  showAddModal.value = false
  newSource.name = ''
  newSource.path = ''
}

const highlightMatch = (text: string) => {
  // Simple highlight logic (in real app, use backend highlights)
  if (!query.value) return text
  const terms = query.value.split(' ').filter(t => t.length > 2)
  let res = text
  // Basic replace for demo (Note: This is a simple implementation)
  terms.forEach(t => {
    const regex = new RegExp(`(${t})`, 'gi')
    res = res.replace(regex, '<span class="text-[var(--accent-primary)] font-bold bg-[var(--accent-surface)]">$1</span>')
  })
  return res
}

function getSourceIcon(type: string) {
  switch(type) {
    case 'folder': return 'folder' // Need folder icon, fallback?
    case 'github': return 'cpu' // fallback
    case 'web': return 'globe' // Need globe icon
    default: return 'file'
  }
}
</script>
