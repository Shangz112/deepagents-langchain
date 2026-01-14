<template>
  <div class="h-full flex flex-col relative overflow-hidden border border-[var(--border-subtle)] rounded-lg bg-[var(--bg-app)] shadow-inner">
    <!-- Toolbar -->
    <div class="absolute top-4 left-4 z-10 flex gap-2">
      <button @click="fitGraph" class="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-[var(--bg-panel)]/80 backdrop-blur border border-[var(--border-subtle)] text-xs font-medium text-[var(--fg-secondary)] hover:text-[var(--fg-primary)] hover:border-[var(--accent-primary)] transition-all shadow-sm">
        <Icon name="maximize" size="14" />
        Fit
      </button>
      <button @click="refreshGraph" class="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-[var(--bg-panel)]/80 backdrop-blur border border-[var(--border-subtle)] text-xs font-medium text-[var(--fg-secondary)] hover:text-[var(--fg-primary)] hover:border-[var(--accent-primary)] transition-all shadow-sm">
        <Icon name="refresh-cw" size="14" />
        Refresh
      </button>
      <div class="flex items-center gap-3 px-3 py-1.5 bg-[var(--bg-panel)]/80 backdrop-blur border border-[var(--border-subtle)] rounded-lg text-xs text-[var(--fg-secondary)] shadow-sm">
        <div class="flex items-center gap-1.5">
          <span class="w-2 h-2 rounded-full bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.5)]"></span>
          User
        </div>
        <div class="flex items-center gap-1.5">
          <span class="w-2 h-2 rounded-full bg-[var(--accent-primary)] shadow-[0_0_8px_rgba(139,92,246,0.5)]"></span>
          Agent
        </div>
        <div class="flex items-center gap-1.5">
          <span class="w-2 h-2 rounded-full bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.5)]"></span>
          Tool
        </div>
      </div>
    </div>

    <!-- Graph Container -->
    <div ref="cyContainer" class="w-full h-full absolute inset-0"></div>

    <!-- Node Details Overlay -->
    <div v-if="selectedNode" class="absolute bottom-4 right-4 w-80 bg-[var(--bg-panel)]/95 backdrop-blur-md border border-[var(--border-subtle)] rounded-xl shadow-2xl p-5 z-20 transition-all animate-in slide-in-from-bottom-4">
      <div class="flex justify-between items-start mb-3">
        <div class="flex items-center gap-2 overflow-hidden">
          <div class="w-8 h-8 rounded-lg bg-[var(--bg-surface)] flex items-center justify-center shrink-0 border border-[var(--border-subtle)]">
             <!-- Dynamic icon based on type -->
             <Icon v-if="selectedNode.data('type') === 'user'" name="user" size="16" class="text-blue-500" />
             <Icon v-else-if="selectedNode.data('type') === 'agent'" name="cpu" size="16" class="text-[var(--accent-primary)]" />
             <Icon v-else-if="selectedNode.data('type') === 'tool'" name="settings" size="16" class="text-amber-500" />
             <Icon v-else name="activity" size="16" class="text-[var(--fg-secondary)]" />
          </div>
          <h3 class="font-bold text-[var(--fg-primary)] truncate">{{ selectedNode.data('label') }}</h3>
        </div>
        <button @click="selectedNode = null" class="text-[var(--fg-tertiary)] hover:text-[var(--fg-primary)] transition-colors">
          <Icon name="x" size="18" />
        </button>
      </div>
      
      <div class="space-y-3 text-xs text-[var(--fg-secondary)] max-h-60 overflow-y-auto custom-scrollbar">
        <div v-if="selectedNode.data('type')">
          <span class="uppercase tracking-wider text-[10px] font-bold text-[var(--fg-tertiary)] mb-1 block">Type</span>
          <div class="px-2 py-1 rounded bg-[var(--bg-surface)] border border-[var(--border-subtle)] inline-block text-[var(--fg-primary)]">{{ selectedNode.data('type') }}</div>
        </div>
        <div v-if="selectedNode.data('content')">
          <span class="uppercase tracking-wider text-[10px] font-bold text-[var(--fg-tertiary)] mb-1 block">Content</span>
          <div class="p-2 rounded bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-[var(--fg-primary)] whitespace-pre-wrap break-words leading-relaxed">{{ selectedNode.data('content') }}</div>
        </div>
         <div v-if="selectedNode.data('meta')">
          <span class="uppercase tracking-wider text-[10px] font-bold text-[var(--fg-tertiary)] mb-1 block">Meta</span>
          <pre class="text-[var(--fg-secondary)] bg-[#000] p-2 rounded border border-[var(--border-subtle)] mt-1 overflow-x-auto font-mono">{{ JSON.stringify(selectedNode.data('meta'), null, 2) }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import cytoscape from 'cytoscape'
import Icon from '../components/common/Icon.vue'

const props = defineProps<{
  messages?: any[]
}>()

const cyContainer = ref<HTMLElement | null>(null)
const cy = ref<cytoscape.Core | null>(null)
const selectedNode = ref<cytoscape.NodeSingular | null>(null)

const updateGraph = () => {
  if (!cy.value) return
  if (!props.messages || props.messages.length === 0) return

  const elements: any[] = []
  let previousNodeId: string | null = null

  props.messages.forEach((msg, index) => {
    const msgNodeId = `msg-${msg.id || index}`
    
    // Message Node
    elements.push({
      data: {
        id: msgNodeId,
        label: msg.role === 'user' ? 'User Input' : 'Agent Response',
        type: msg.role === 'user' ? 'user' : 'assistant',
        content: msg.content,
        timestamp: new Date(msg.timestamp).toLocaleTimeString()
      }
    })

    if (previousNodeId) {
      elements.push({ data: { source: previousNodeId, target: msgNodeId } })
    }
    previousNodeId = msgNodeId

    // Tool Events
    if (msg.toolEvents && msg.toolEvents.length > 0) {
      let previousToolId = msgNodeId
      
      msg.toolEvents.forEach((tool: any, tIndex: number) => {
        const toolNodeId = `tool-${tool.id || tIndex}`
        
        elements.push({
          data: {
            id: toolNodeId,
            label: tool.name,
            type: 'tool',
            content: JSON.stringify(tool.input),
            meta: tool,
            timestamp: new Date(tool.timestamp).toLocaleTimeString()
          }
        })
        
        elements.push({ data: { source: previousToolId, target: toolNodeId } })
        previousToolId = toolNodeId
        
        // Result Node if completed
        if (tool.status === 'completed' || tool.output) {
          const resNodeId = `res-${tool.id || tIndex}`
          elements.push({
            data: {
              id: resNodeId,
              label: 'Result',
              type: 'tool-result',
              content: typeof tool.output === 'string' ? tool.output : JSON.stringify(tool.output),
              timestamp: new Date().toLocaleTimeString()
            }
          })
          elements.push({ data: { source: toolNodeId, target: resNodeId } })
        }
      })
    }
  })

  cy.value.json({ elements })
  cy.value.layout({
    name: 'breadthfirst',
    directed: true,
    padding: 50,
    spacingFactor: 1.5,
    animate: true,
    animationDuration: 500
  }).run()
}

const initCytoscape = () => {
  if (!cyContainer.value) return

  cy.value = cytoscape({
    container: cyContainer.value,
    style: [
      {
        selector: 'node',
        style: {
          'label': 'data(label)',
          'color': '#a1a1aa', // zinc-400
          'font-size': '12px',
          'text-valign': 'bottom',
          'text-margin-y': 8,
          'background-color': '#27272a', // zinc-800
          'width': 48,
          'height': 48,
          'border-width': 1,
          'border-color': '#52525b', // zinc-600
          'overlay-opacity': 0
        }
      },
      {
        selector: 'node:selected',
        style: {
          'border-width': 2,
          'border-color': '#8b5cf6', // violet-500
          'color': '#fff'
        }
      },
      {
        selector: 'node[type="user"]',
        style: {
          'background-color': '#1e3a8a', // blue-900
          'border-color': '#3b82f6', // blue-500
          'color': '#60a5fa', // blue-400
          'shape': 'ellipse'
        }
      },
      {
        selector: 'node[type="assistant"]',
        style: {
          'background-color': '#4c1d95', // violet-900
          'border-color': '#8b5cf6', // violet-500
          'color': '#a78bfa', // violet-400
          'shape': 'hexagon'
        }
      },
      {
        selector: 'node[type="tool"]',
        style: {
          'background-color': '#451a03', // amber-900
          'border-color': '#f59e0b', // amber-500
          'color': '#fbbf24', // amber-400
          'shape': 'rectangle'
        }
      },
      {
        selector: 'node[type="tool-result"]',
        style: {
          'background-color': '#14532d', // green-900
          'border-color': '#22c55e', // green-500
          'color': '#4ade80', // green-400
          'shape': 'round-rectangle'
        }
      },
      {
        selector: 'edge',
        style: {
          'width': 2,
          'line-color': '#3f3f46', // zinc-700
          'target-arrow-color': '#3f3f46',
          'target-arrow-shape': 'triangle',
          'curve-style': 'bezier',
          'arrow-scale': 1.2
        }
      },
      {
        selector: 'edge:selected',
        style: {
          'line-color': '#8b5cf6',
          'target-arrow-color': '#8b5cf6'
        }
      }
    ]
  })

  cy.value.on('tap', 'node', (evt: any) => {
    selectedNode.value = evt.target
  })
  
  cy.value.on('tap', (evt: any) => {
    if (evt.target === cy.value) {
      selectedNode.value = null
    }
  })

  if (props.messages && props.messages.length > 0) {
    updateGraph()
  }
}

watch(() => props.messages, () => {
  updateGraph()
}, { deep: true })

const fitGraph = () => {
  if (cy.value) {
    cy.value.fit(undefined, 50)
  }
}

const refreshGraph = () => {
  updateGraph()
}

onMounted(() => {
  initCytoscape()
})

onUnmounted(() => {
  if (cy.value) {
    cy.value.destroy()
  }
})
</script>

<style scoped></style>
