<template>
  <div class="markdown-content space-y-3">
    <template v-for="(block, index) in parsedBlocks" :key="index">
      <!-- Code Block -->
      <div v-if="block.type === 'code'" class="rounded-lg overflow-hidden border border-[var(--border-subtle)] bg-[#1e1e1e] my-2">
        <div class="flex items-center justify-between px-3 py-1.5 bg-[#2d2d2d] border-b border-white/5">
          <span class="text-xs font-mono text-gray-400">{{ block.lang || 'code' }}</span>
          <button 
            @click="copyToClipboard(block.content, index)" 
            class="text-[10px] uppercase font-bold tracking-wider text-gray-500 hover:text-white transition-colors flex items-center gap-1"
          >
            <span v-if="copiedIndex === index" class="text-emerald-400">Copied!</span>
            <span v-else>Copy</span>
          </button>
        </div>
        <div class="p-3 overflow-x-auto custom-scrollbar">
          <pre><code class="font-mono text-sm leading-relaxed text-gray-300 whitespace-pre">{{ block.content }}</code></pre>
        </div>
      </div>

      <!-- Text Block -->
      <div v-else class="whitespace-pre-wrap break-words leading-relaxed" v-html="renderInline(block.content)"></div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

const props = defineProps<{
  content: string
}>()

const copiedIndex = ref<number | null>(null)

interface Block {
  type: 'text' | 'code'
  content: string
  lang?: string
}

const parsedBlocks = computed(() => {
  if (!props.content) return []
  
  const blocks: Block[] = []
  // Split by code blocks
  const regex = /```(\w+)?\n([\s\S]*?)```/g
  
  let lastIndex = 0
  let match
  
  while ((match = regex.exec(props.content)) !== null) {
    // Add preceding text
    if (match.index > lastIndex) {
      blocks.push({
        type: 'text',
        content: props.content.slice(lastIndex, match.index)
      })
    }
    
    // Add code block
    blocks.push({
      type: 'code',
      lang: match[1],
      content: match[2].trim() // Trim newline at end
    })
    
    lastIndex = regex.lastIndex
  }
  
  // Add remaining text
  if (lastIndex < props.content.length) {
    blocks.push({
      type: 'text',
      content: props.content.slice(lastIndex)
    })
  }
  
  return blocks
})

function escapeHtml(text: string) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function renderInline(text: string) {
  // 1. Escape HTML first to prevent XSS
  let html = escapeHtml(text)
  
  // 2. Inline Code `code`
  html = html.replace(/`([^`]+)`/g, '<code class="bg-black/20 px-1.5 py-0.5 rounded text-[var(--accent-primary)] font-mono text-xs border border-[var(--accent-primary)]/20">$1</code>')
  
  // 3. Bold **text**
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
  
  // 4. Italic *text*
  html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>')
  
  // 5. Links [text](url)
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" class="text-[var(--accent-primary)] hover:underline decoration-dashed underline-offset-4">$1</a>')
  
  // 6. Headers
  // We handle headers roughly by just making them bold and larger
  html = html.replace(/^### (.*$)/gm, '<h3 class="text-sm font-bold mt-4 mb-2">$1</h3>')
  html = html.replace(/^## (.*$)/gm, '<h2 class="text-base font-bold mt-5 mb-2 border-b border-white/10 pb-1">$1</h2>')
  html = html.replace(/^# (.*$)/gm, '<h1 class="text-lg font-bold mt-6 mb-3 border-b border-white/10 pb-2">$1</h1>')
  
  // 7. Lists
  // Simple replacement for bullet points at start of line
  html = html.replace(/^- (.*$)/gm, '<li class="ml-4 list-disc marker:text-[var(--fg-tertiary)]">$1</li>')
  
  // 8. Blockquotes
  html = html.replace(/^> (.*$)/gm, '<blockquote class="border-l-2 border-[var(--accent-primary)] pl-3 italic text-gray-400 my-2">$1</blockquote>')

  // 9. Horizontal Rule
  html = html.replace(/^---$/gm, '<hr class="border-white/10 my-4">')

  return html
}

function copyToClipboard(text: string, index: number) {
  navigator.clipboard.writeText(text).then(() => {
    copiedIndex.value = index
    setTimeout(() => {
      copiedIndex.value = null
    }, 2000)
  })
}
</script>

<style scoped>
.markdown-content :deep(ul) {
  margin-top: 0.5rem;
  margin-bottom: 0.5rem;
}
.markdown-content :deep(li) {
  margin-bottom: 0.25rem;
}
.custom-scrollbar::-webkit-scrollbar {
  height: 6px;
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #4b5563;
  border-radius: 3px;
}
</style>
