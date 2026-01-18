<template>
  <div class="flex flex-col h-full overflow-hidden">
    <!-- Header -->
    <div class="p-3 border-b border-[var(--border-subtle)] flex items-center justify-between gap-2">
      <div v-if="isSelectionMode" class="flex items-center gap-2 flex-1">
         <span class="text-xs font-bold text-[var(--fg-primary)]">{{ selectedIds.size }} selected</span>
         <div class="flex-1"></div>
         <button 
           @click="deleteSelected" 
           class="p-1.5 rounded-md hover:bg-red-500/10 text-red-500 transition-colors"
           title="Delete Selected"
           :disabled="selectedIds.size === 0"
         >
           <Icon name="trash" size="16" />
         </button>
         <button 
           @click="toggleSelectionMode" 
           class="p-1.5 rounded-md hover:bg-[var(--bg-hover)] text-[var(--fg-secondary)] transition-colors"
           title="Cancel"
         >
           <Icon name="x" size="16" />
         </button>
      </div>
      <div v-else class="flex items-center justify-between w-full">
        <h3 class="text-xs font-bold text-[var(--fg-tertiary)] uppercase tracking-wider">History</h3>
        <div class="flex gap-1">
            <button 
                @click="toggleSelectionMode" 
                class="p-1.5 rounded-md hover:bg-[var(--bg-hover)] text-[var(--fg-secondary)] transition-colors"
                title="Batch Manage"
            >
                <Icon name="check-square" size="16" />
            </button>
            <button 
                @click="createSession" 
                class="p-1.5 rounded-md hover:bg-[var(--bg-hover)] text-[var(--fg-secondary)] hover:text-[var(--accent-primary)] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                title="New Chat"
                :disabled="isCreating"
            >
                <Icon name="plus" size="16" />
            </button>
        </div>
      </div>
    </div>

    <!-- List -->
    <div class="flex-1 overflow-y-auto p-2 space-y-1">
      <div 
        v-for="session in sessions" 
        :key="session.id"
        class="group flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm transition-all duration-200 cursor-pointer border border-transparent relative"
        :class="session.id === currentSessionId ? 'bg-[var(--bg-surface)] border-[var(--border-subtle)] shadow-sm' : 'hover:bg-[var(--bg-hover)] text-[var(--fg-secondary)]'"
        @click="handleItemClick(session.id)"
      >
        <!-- Checkbox for selection mode -->
        <div v-if="isSelectionMode" class="shrink-0 mr-1" @click.stop>
            <input 
                type="checkbox" 
                :checked="selectedIds.has(session.id)"
                @change="toggleSelection(session.id)"
                class="rounded border-[var(--border-subtle)] bg-[var(--bg-app)] text-[var(--accent-primary)] focus:ring-[var(--accent-primary)]"
            />
        </div>

        <div class="shrink-0 text-[var(--fg-tertiary)]">
          <Icon name="message-square" size="16" />
        </div>
        
        <div class="flex-1 min-w-0 flex flex-col gap-0.5">
          <div v-if="editingId === session.id" class="flex items-center gap-1" @click.stop>
            <input 
              v-model="editingTitle"
              class="w-full bg-[var(--bg-app)] border border-[var(--accent-primary)] rounded px-1 py-0.5 text-xs focus:outline-none text-[var(--fg-primary)]"
              @keyup.enter="saveEdit"
              @keyup.esc="cancelEdit"
              @blur="saveEdit"
              ref="editInput"
              autoFocus
            />
          </div>
          <span v-else class="truncate font-medium" :class="session.id === currentSessionId ? 'text-[var(--fg-primary)]' : ''">
            {{ session.name || 'New Chat' }}
          </span>
          <span class="text-[10px] text-[var(--fg-tertiary)] truncate">
            {{ formatDate(session.updated_at || session.created_at) }}
          </span>
        </div>

        <!-- Action buttons (hidden in selection mode) -->
        <div v-if="!isSelectionMode" class="flex items-center opacity-0 group-hover:opacity-100 transition-opacity gap-1">
            <button 
              v-if="editingId !== session.id"
              class="p-1.5 rounded-md hover:bg-[var(--bg-app)] text-[var(--fg-tertiary)] hover:text-[var(--accent-primary)] transition-all"
              @click.stop="startEdit(session)"
              title="Rename"
            >
              <Icon name="edit" size="14" />
            </button>
            <button 
              class="p-1.5 rounded-md hover:bg-[var(--bg-app)] text-[var(--fg-tertiary)] hover:text-red-500 transition-all"
              @click.stop="deleteSession(session.id)"
              title="Delete"
            >
              <Icon name="trash" size="14" />
            </button>
        </div>
      </div>

      <div v-if="sessions.length === 0" class="text-center py-8 text-[var(--fg-tertiary)] text-xs">
        No history yet
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, nextTick, reactive } from 'vue'
import { sessionStore } from '../../store'
import Icon from '../common/Icon.vue'

const sessions = computed(() => sessionStore.sessions)
const currentSessionId = computed(() => sessionStore.sessionId)
const editingId = ref<string | null>(null)
const editingTitle = ref('')
const editInput = ref<HTMLInputElement | null>(null)

// Selection Mode State
const isSelectionMode = ref(false)
const selectedIds = reactive(new Set<string>())
const isCreating = ref(false)

const emit = defineEmits(['select'])

onMounted(() => {
  sessionStore.loadSessions()
})

function toggleSelectionMode() {
    isSelectionMode.value = !isSelectionMode.value
    selectedIds.clear()
}

function toggleSelection(id: string) {
    if (selectedIds.has(id)) {
        selectedIds.delete(id)
    } else {
        selectedIds.add(id)
    }
}

function handleItemClick(id: string) {
    if (isSelectionMode.value) {
        toggleSelection(id)
    } else {
        emit('select', id)
    }
}

async function createSession() {
  if (isCreating.value) return
  isCreating.value = true
  try {
    const id = await sessionStore.createSession()
    emit('select', id)
  } catch (e) {
    console.error(e)
  } finally {
    isCreating.value = false
  }
}

async function deleteSession(id: string) {
  if (confirm('Are you sure you want to delete this session?')) {
    await sessionStore.deleteSession(id)
  }
}

async function deleteSelected() {
    if (selectedIds.size === 0) return
    
    if (confirm(`Are you sure you want to delete ${selectedIds.size} sessions?`)) {
        const ids = Array.from(selectedIds)
        await sessionStore.deleteSessions(ids)
        
        selectedIds.clear()
        isSelectionMode.value = false
    }
}

function startEdit(session: any) {
    editingId.value = session.id
    editingTitle.value = session.name || 'New Chat'
    nextTick(() => {
        // Autofocus logic handled by template autoFocus attribute
    })
}

async function saveEdit() {
    if (!editingId.value) return
    
    const newTitle = editingTitle.value.trim()
    if (newTitle && newTitle !== (sessions.value.find(s => s.id === editingId.value)?.name || 'New Chat')) {
        await sessionStore.renameSession(editingId.value, newTitle)
    }
    editingId.value = null
    editingTitle.value = ''
}

function cancelEdit() {
    editingId.value = null
    editingTitle.value = ''
}

function formatDate(ts: number) {
  if (!ts) return ''
  const d = new Date(ts)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  
  if (diff < 24 * 3600 * 1000 && now.getDate() === d.getDate()) {
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }
  return d.toLocaleDateString([], { month: 'short', day: 'numeric' })
}
</script>
