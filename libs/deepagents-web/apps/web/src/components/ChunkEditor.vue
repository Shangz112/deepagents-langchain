<template>
  <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
    <div class="bg-[var(--bg-app)] w-[95vw] h-[90vh] rounded-xl shadow-2xl flex flex-col overflow-hidden border border-[var(--border-subtle)]">
      <!-- Header -->
      <div class="flex items-center justify-between p-4 border-b border-[var(--border-subtle)] bg-[var(--bg-panel)]">
        <h3 class="font-bold text-lg text-[var(--fg-primary)] flex items-center gap-2">
          <Icon name="edit" size="20" class="text-[var(--accent-primary)]" />
          Chunk Editor & Preview: {{ sourceName }}
        </h3>
        <button @click="$emit('close')" class="btn btn-sm btn-ghost">
          <Icon name="x" size="20" />
        </button>
      </div>

      <!-- Content -->
      <div class="flex-1 flex overflow-hidden">
        <!-- Left: Chunks List -->
        <div class="w-1/3 flex flex-col border-r border-[var(--border-subtle)] bg-[var(--bg-surface)]">
          <div class="p-3 border-b border-[var(--border-subtle)] font-bold text-xs uppercase text-[var(--fg-tertiary)] flex justify-between items-center">
            <span>Chunks ({{ chunks.length }})</span>
            <span v-if="loading" class="text-[var(--accent-primary)] animate-pulse">Loading...</span>
          </div>
          <div class="flex-1 overflow-y-auto p-2 space-y-3">
            <div v-for="chunk in paginatedChunks" :key="chunk.id" 
                 class="p-3 rounded bg-[var(--bg-app)] border border-[var(--border-subtle)] hover:border-[var(--accent-primary)] transition-colors group relative"
                 :class="{'ring-2 ring-[var(--accent-primary)]': activeChunkId === chunk.id}"
                 @click="activeChunkId = chunk.id"
            >
              <div class="flex justify-between items-center mb-2">
                <span class="text-sm font-bold text-[var(--fg-primary)]">#{{ chunk.index }}</span>
                <span class="text-xs text-[var(--fg-tertiary)]">{{ chunk.id ? chunk.id.substring(0,8) + '...' : 'No ID' }}</span>
              </div>
              <textarea 
                v-model="chunk.content" 
                class="w-full bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded p-2 text-sm text-[var(--fg-primary)] focus:border-[var(--accent-primary)] outline-none resize-y min-h-[120px]"
                @click.stop
              ></textarea>
              <div class="mt-2 flex justify-end">
                <button @click.stop="saveChunk(chunk)" class="px-2 py-1 rounded bg-[var(--accent-primary)] text-white text-xs font-medium opacity-0 group-hover:opacity-100 transition-opacity">
                  Save
                </button>
              </div>
            </div>
          </div>
          <!-- Pagination Controls -->
          <div class="p-3 border-t border-[var(--border-subtle)] bg-[var(--bg-surface)] flex justify-between items-center">
            <button 
                @click="prevPage" 
                :disabled="currentPage === 1" 
                class="px-3 py-1 rounded border border-[var(--border-subtle)] text-sm text-[var(--fg-secondary)] hover:bg-[var(--bg-subtle)] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
                Previous
            </button>
            <span class="text-xs text-[var(--fg-tertiary)] font-medium">Page {{ currentPage }} of {{ totalPages }}</span>
            <button 
                @click="nextPage" 
                :disabled="currentPage === totalPages" 
                class="px-3 py-1 rounded border border-[var(--border-subtle)] text-sm text-[var(--fg-secondary)] hover:bg-[var(--bg-subtle)] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
                Next
            </button>
          </div>
        </div>

        <!-- Right: File Preview -->
        <div class="flex-1 bg-white flex flex-col relative overflow-hidden">
             <div v-if="loading && !fileUrl" class="flex items-center justify-center h-full text-[var(--fg-tertiary)]">
                <Icon name="loader" class="animate-spin mr-2" /> Loading preview...
             </div>
             
             <!-- Use VueOfficeDocx for DOCX, VueOfficePdf for PDF, iframe for others or text -->
             <component 
               v-else-if="previewComponent && fileUrl"
               :is="previewComponent"
               :src="fileUrl"
               class="flex-1 w-full h-full overflow-auto"
               style="height: 100%;"
               @rendered="handleRendered"
               @error="handleError"
             />
             
             <div v-else-if="fileType === 'text' && textContent" class="p-8 whitespace-pre-wrap font-mono text-sm overflow-auto text-black h-full">
                {{ textContent }}
             </div>
             
             <div v-else-if="renderError" class="flex flex-col items-center justify-center h-full text-red-500 p-4 text-center">
                <Icon name="alert-circle" size="32" class="mb-2" />
                <p>Failed to render document.</p>
                <p class="text-xs mt-1 text-gray-500">{{ renderError }}</p>
             </div>

             <div v-else class="flex items-center justify-center h-full text-gray-500">
                <span v-if="!fileUrl && !loading">Preview not available (File load failed).</span>
                <span v-else>Preview not available for this file type ({{ fileType }}).</span>
             </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from 'vue'
import Icon from './common/Icon.vue'
import axios from 'axios'
import VueOfficeDocx from '@vue-office/docx'
import '@vue-office/docx/lib/index.css'
import VueOfficePdf from '@vue-office/pdf'

const props = defineProps<{
  sourceId: string,
  sourceName: string,
  visible: boolean
}>()

const emit = defineEmits(['close'])

const chunks = ref<any[]>([])
const loading = ref(false)
const activeChunkId = ref<string | null>(null)
const fileUrl = ref('')
const textContent = ref('')
const renderError = ref<string | null>(null)

// Pagination
const currentPage = ref(1)
const pageSize = 3

const totalPages = computed(() => Math.ceil(chunks.value.length / pageSize) || 1)

const paginatedChunks = computed(() => {
    const start = (currentPage.value - 1) * pageSize
    return chunks.value.slice(start, start + pageSize)
})

const nextPage = () => {
    if (currentPage.value < totalPages.value) currentPage.value++
}

const prevPage = () => {
    if (currentPage.value > 1) currentPage.value--
}

const fileType = computed(() => {
    if (!props.sourceName) return 'unknown'
    const ext = props.sourceName.split('.').pop()?.toLowerCase()
    if (ext === 'docx') return 'docx'
    if (ext === 'pdf') return 'pdf'
    if (['txt', 'md', 'json', 'py', 'js', 'ts', 'xml', 'yml', 'yaml'].includes(ext || '')) return 'text'
    return 'unknown'
})

const previewComponent = computed(() => {
    if (fileType.value === 'docx') return VueOfficeDocx
    if (fileType.value === 'pdf') return VueOfficePdf
    return null
})

onUnmounted(() => {
    if (fileUrl.value) URL.revokeObjectURL(fileUrl.value)
})

watch(() => props.visible, async (val) => {
  if (val && props.sourceId) {
    await loadData()
  }
})

const handleRendered = () => {
    console.log('Document rendered successfully')
    renderError.value = null
}

const handleError = (err: any) => {
    console.error('Document render error:', err)
    renderError.value = err?.message || 'Unknown render error'
}

const loadData = async () => {
    loading.value = true
    renderError.value = null
    // Reset pagination
    currentPage.value = 1
    
    try {
        // Fetch chunks
        const r = await axios.get(`/api/v1/kb/sources/${props.sourceId}/chunks`)
        chunks.value = r.data
        
        // Fetch file as Blob for robust rendering
        const fileRes = await axios.get(`/api/v1/kb/sources/${props.sourceId}/file`, {
            responseType: 'blob'
        })
        const blob = new Blob([fileRes.data], { type: fileRes.headers['content-type'] })
        fileUrl.value = URL.createObjectURL(blob)
        
        if (fileType.value === 'text') {
             // For text, we can read the blob text
             textContent.value = await blob.text()
        }

    } catch (e) {
        console.error("Failed to load chunks/file", e)
    } finally {
        loading.value = false
    }
}

const saveChunk = async (chunk: any) => {
    try {
        await axios.put(`/api/v1/kb/chunks/${chunk.id}`, { text: chunk.content })
        alert('Chunk saved!')
    } catch (e) {
        alert('Failed to save chunk')
    }
}

const deleteChunk = async (chunk: any) => {
    try {
        await axios.delete(`/api/v1/kb/chunks/${chunk.id}`)
        alert('Chunk deleted!')
        // Remove chunk from local state
        chunks.value = chunks.value.filter(c => c.id !== chunk.id)
    } catch (e) {
        alert('Failed to delete chunk')
    }
}
</script>
