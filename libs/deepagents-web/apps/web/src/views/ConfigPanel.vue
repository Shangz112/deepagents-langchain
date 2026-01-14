<template>
  <div class="h-full flex flex-col overflow-hidden bg-[var(--bg-app)]">
    <!-- Header -->
    <header class="flex-none p-6 border-b border-[var(--border-subtle)] bg-[var(--bg-panel)]/80 backdrop-blur-md z-10">
      <div class="flex justify-between items-center max-w-5xl mx-auto w-full">
        <div>
          <h1 class="text-2xl font-bold text-[var(--fg-primary)] tracking-tight flex items-center gap-3">
            <div class="p-2 rounded-lg bg-[var(--accent-surface)] text-[var(--accent-primary)]">
              <Icon name="settings" size="24" />
            </div>
            System Configuration
          </h1>
          <p class="text-[var(--fg-secondary)] text-sm mt-1 ml-12">Manage models, middleware, and backend settings</p>
        </div>
        <div class="flex gap-3">
          <button @click="load" class="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium text-[var(--fg-secondary)] hover:text-[var(--fg-primary)] hover:bg-[var(--bg-hover)] transition-colors border border-transparent hover:border-[var(--border-subtle)]" :disabled="isLoading">
            <Icon name="refresh-cw" size="16" :class="isLoading ? 'animate-spin' : ''" />
            Reset
          </button>
          <button @click="save" class="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-[var(--accent-primary)] text-white hover:bg-[var(--accent-hover)] shadow-lg shadow-[var(--accent-glow)] transition-all" :disabled="isSaving">
            <Icon v-if="isSaving" name="refresh-cw" size="16" class="animate-spin" />
            <Icon v-else name="save" size="16" /> 
            {{ isSaving ? 'Saving...' : 'Save Changes' }}
          </button>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="flex-1 overflow-y-auto p-6">
      <div class="max-w-5xl mx-auto space-y-8">
        
        <!-- Model Settings -->
        <section class="p-6 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] shadow-sm">
          <h2 class="text-lg font-semibold text-[var(--fg-primary)] mb-6 flex items-center">
            <span class="w-1 h-6 bg-[var(--accent-primary)] rounded-full mr-3"></span>
            Model Parameters
          </h2>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="space-y-2">
              <label class="text-sm font-medium text-[var(--fg-secondary)]">Model Provider</label>
              <div class="relative">
                <select v-model="cfg.modelProvider" class="w-full bg-[var(--bg-app)] border border-[var(--border-subtle)] rounded-lg px-4 py-2.5 text-[var(--fg-primary)] focus:border-[var(--accent-primary)] focus:ring-1 focus:ring-[var(--accent-primary)] outline-none transition-all appearance-none">
                  <option value="openai">OpenAI</option>
                  <option value="anthropic">Anthropic</option>
                  <option value="azure">Azure OpenAI</option>
                  <option value="siliconflow">SiliconFlow</option>
                  <option value="local">Local (Ollama/vLLM)</option>
                </select>
                <Icon name="chevron-down" size="16" class="absolute right-3 top-3 text-[var(--fg-tertiary)] pointer-events-none" />
              </div>
            </div>
            
            <div v-if="cfg.modelProvider === 'siliconflow'" class="col-span-1 md:col-span-2 space-y-4 p-4 bg-[var(--bg-app)] rounded-lg border border-[var(--border-subtle)]">
              <h3 class="text-sm font-semibold text-[var(--fg-primary)]">SiliconFlow Settings</h3>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="space-y-2">
                  <label class="text-sm font-medium text-[var(--fg-secondary)]">API Key</label>
                  <input v-model="cfg.apiKey" type="password" class="w-full bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-lg px-4 py-2 text-[var(--fg-primary)] focus:border-[var(--accent-primary)] outline-none" placeholder="sk-..." />
                </div>
                <div class="space-y-2">
                  <label class="text-sm font-medium text-[var(--fg-secondary)]">Base URL</label>
                  <input v-model="cfg.baseUrl" type="text" class="w-full bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-lg px-4 py-2 text-[var(--fg-primary)] focus:border-[var(--accent-primary)] outline-none" placeholder="https://api.siliconflow.cn/v1" />
                </div>
              </div>
            </div>

            <div class="space-y-2">
              <label class="text-sm font-medium text-[var(--fg-secondary)]">Model Name</label>
              <input v-model="cfg.modelName" type="text" class="w-full bg-[var(--bg-app)] border border-[var(--border-subtle)] rounded-lg px-4 py-2.5 text-[var(--fg-primary)] focus:border-[var(--accent-primary)] focus:ring-1 focus:ring-[var(--accent-primary)] outline-none transition-all placeholder-[var(--fg-tertiary)]" placeholder="e.g. gpt-4-turbo" />
            </div>
            <div class="space-y-2">
              <label class="text-sm font-medium text-[var(--fg-secondary)] flex justify-between">
                Temperature
                <span class="text-[var(--accent-primary)] font-mono bg-[var(--accent-surface)] px-2 rounded">{{ cfg.temperature }}</span>
              </label>
              <input v-model.number="cfg.temperature" type="range" min="0" max="1" step="0.1" class="w-full accent-[var(--accent-primary)] h-2 bg-[var(--bg-hover)] rounded-lg appearance-none cursor-pointer" />
            </div>
            <div class="space-y-2">
              <label class="text-sm font-medium text-[var(--fg-secondary)]">Max Tokens</label>
              <input v-model.number="cfg.maxTokens" type="number" class="w-full bg-[var(--bg-app)] border border-[var(--border-subtle)] rounded-lg px-4 py-2.5 text-[var(--fg-primary)] focus:border-[var(--accent-primary)] focus:ring-1 focus:ring-[var(--accent-primary)] outline-none transition-all" />
            </div>
          </div>
        </section>

        <!-- Middleware Configuration -->
        <section class="p-6 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] shadow-sm">
          <h2 class="text-lg font-semibold text-[var(--fg-primary)] mb-6 flex items-center">
            <span class="w-1 h-6 bg-purple-500 rounded-full mr-3"></span>
            Middleware Pipeline
          </h2>
          <div class="space-y-3">
            <div v-for="(mw, index) in cfg.middleware" :key="index" class="flex items-center justify-between p-4 bg-[var(--bg-app)] rounded-lg border border-[var(--border-subtle)] hover:border-[var(--accent-primary)]/50 transition-all group">
              <div class="flex items-center gap-4">
                <div class="cursor-move text-[var(--fg-tertiary)] group-hover:text-[var(--fg-secondary)]">
                  <Icon name="menu" size="16" />
                </div>
                <div>
                  <div class="font-medium text-[var(--fg-primary)]">{{ mw.name }}</div>
                  <div class="text-xs text-[var(--fg-secondary)]">{{ mw.description }}</div>
                </div>
              </div>
              <label class="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" v-model="mw.enabled" class="sr-only peer">
                <div class="w-11 h-6 bg-[var(--bg-hover)] peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[var(--accent-primary)]"></div>
              </label>
            </div>
          </div>
        </section>

        <!-- Backend & Environment -->
        <section class="p-6 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] shadow-sm">
          <h2 class="text-lg font-semibold text-[var(--fg-primary)] mb-6 flex items-center">
            <span class="w-1 h-6 bg-blue-500 rounded-full mr-3"></span>
            Environment & Sandbox
          </h2>
          <div class="grid grid-cols-1 gap-6">
             <div class="flex items-center justify-between p-4 bg-[var(--bg-app)] rounded-lg border border-[var(--border-subtle)]">
              <div class="flex items-center gap-4">
                <div class="p-2 rounded bg-blue-500/10 text-blue-500">
                  <Icon name="cpu" size="20" />
                </div>
                <div>
                  <div class="font-medium text-[var(--fg-primary)]">Code Sandbox</div>
                  <div class="text-xs text-[var(--fg-secondary)]">Execute code in isolated Docker containers</div>
                </div>
              </div>
               <div class="flex items-center gap-3">
                  <span class="px-2 py-1 rounded text-xs bg-[var(--success)]/10 text-[var(--success)] border border-[var(--success)]/20 flex items-center gap-1">
                    <span class="w-1.5 h-1.5 rounded-full bg-[var(--success)]"></span>
                    Active
                  </span>
                  <button class="text-xs text-[var(--fg-secondary)] hover:text-[var(--fg-primary)] underline">Configure</button>
               </div>
            </div>
            
             <div class="space-y-2">
               <label class="text-sm font-medium text-[var(--fg-secondary)]">API Endpoint</label>
               <div class="flex gap-2">
                 <input v-model="cfg.apiEndpoint" type="text" class="flex-1 bg-[var(--bg-app)] border border-[var(--border-subtle)] rounded-lg px-4 py-2.5 text-[var(--fg-primary)] focus:border-[var(--accent-primary)] focus:ring-1 focus:ring-[var(--accent-primary)] outline-none transition-all font-mono text-sm" />
                 <button class="px-4 py-2 rounded-lg border border-[var(--border-subtle)] text-[var(--fg-secondary)] hover:text-[var(--fg-primary)] hover:bg-[var(--bg-hover)] transition-colors">Test</button>
               </div>
             </div>
          </div>
        </section>

      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import axios from 'axios'
import Icon from '../components/common/Icon.vue'

const isLoading = ref(false)
const isSaving = ref(false)

const cfg = reactive({
  modelProvider: 'openai',
  modelName: 'gpt-4-turbo',
  apiKey: '',
  baseUrl: 'https://api.siliconflow.cn/v1',
  temperature: 0.7,
  maxTokens: 2048,
  apiEndpoint: 'http://localhost:8000/api/v1',
  middleware: [
    { name: 'Safety Filter', description: 'Blocks harmful content', enabled: true },
    { name: 'Context Compressor', description: 'Summarizes history to save tokens', enabled: true },
    { name: 'PII Redaction', description: 'Masks sensitive personal information', enabled: false },
    { name: 'Logging', description: 'Records interaction logs', enabled: true }
  ]
})

onMounted(() => {
  load()
})

async function load() {
  isLoading.value = true
  try {
    const r = await axios.get('/api/v1/config')
    // Merge response with default structure to ensure UI doesn't break if backend is empty
    if (r.data && Object.keys(r.data).length > 0) {
      Object.assign(cfg, r.data)
    }
  } catch (e) {
    console.error('Failed to load config', e)
  } finally {
    isLoading.value = false
  }
}

async function save() {
  isSaving.value = true
  try {
    await axios.put('/api/v1/config', cfg)
    // Could show a toast here
  } catch (e) {
    console.error('Failed to save config', e)
  } finally {
    isSaving.value = false
  }
}
</script>

<style scoped></style>
