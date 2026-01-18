<template>
  <div class="h-screen w-screen overflow-hidden flex flex-col bg-[var(--bg-app)] text-[var(--fg-primary)] font-sans selection:bg-[var(--accent-surface)] selection:text-[var(--accent-primary)]">
    <!-- Header -->
    <header class="h-16 border-b border-[var(--border-subtle)] bg-[var(--bg-panel)]/80 backdrop-blur-md flex-none z-50 relative shadow-sm shrink-0">
      <div class="w-full h-full flex items-center px-4 gap-4">
        <!-- Mobile Menu Button -->
        <button class="md:hidden p-2 text-[var(--fg-secondary)] hover:text-[var(--fg-primary)] transition-colors" @click="mobileMenuOpen = !mobileMenuOpen">
          <Icon name="menu" size="24" />
        </button>

        <!-- Logo -->
        <div class="flex items-center gap-2 font-bold text-xl tracking-tight select-none">
          <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-[var(--accent-primary)] to-[var(--accent-hover)] flex items-center justify-center text-white shadow-lg shadow-[var(--accent-glow)]">
            <Icon name="zap" size="18" />
          </div>
          <span class="bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-400">DeepAgents</span>
        </div>

        <!-- Desktop Nav (Optional top links) -->
        <div class="hidden md:flex items-center gap-6 ml-8 text-sm font-medium text-[var(--fg-secondary)]">
          <!-- Add top links if needed -->
        </div>

        <div class="ml-auto flex items-center gap-4">
          <!-- Status Indicators -->
          <div class="hidden sm:flex items-center gap-3 text-[10px] font-mono uppercase tracking-wider">
             <div class="flex items-center gap-1.5 px-2 py-1 rounded-full bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-[var(--success)]">
               <span class="relative flex h-2 w-2">
                  <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                  <span class="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                </span>
               <span>Agent Active</span>
             </div>
             <div class="flex items-center gap-1.5 px-2 py-1 rounded-full bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-[var(--fg-tertiary)]">
               <Icon name="cpu" size="12" />
               <span>Tools Ready</span>
             </div>
          </div>
          
          <!-- User Profile / Settings -->
          <button class="w-9 h-9 rounded-full bg-[var(--bg-surface)] border border-[var(--border-subtle)] flex items-center justify-center text-xs font-medium text-[var(--fg-secondary)] hover:text-white hover:border-[var(--accent-primary)] hover:bg-[var(--accent-surface)] transition-all duration-300 shadow-sm">
            DA
          </button>
        </div>
      </div>
    </header>

    <!-- Mobile Navigation Drawer -->
    <div v-if="mobileMenuOpen" class="fixed inset-0 z-40 md:hidden">
      <div class="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity" @click="mobileMenuOpen = false"></div>
      <aside class="absolute top-16 left-0 bottom-0 w-64 bg-[var(--bg-panel)] border-r border-[var(--border-subtle)] p-4 overflow-y-auto animate-in slide-in-from-left-10 shadow-2xl">
         <nav class="grid gap-2">
            <RouterLink v-for="link in links" :key="link.path" :to="link.path" 
              class="group flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium text-[var(--fg-secondary)] hover:text-white hover:bg-[var(--bg-hover)] transition-all duration-200"
              active-class="bg-[var(--accent-surface)] text-[var(--accent-primary)] border border-[var(--accent-primary)]/20"
              @click="mobileMenuOpen = false"
            >
              <Icon :name="link.icon" size="18" class="group-hover:scale-110 transition-transform duration-200" />
              {{ link.name }}
            </RouterLink>
         </nav>
      </aside>
    </div>

    <!-- Main Layout Grid -->
    <div class="flex-1 overflow-hidden grid transition-all duration-300" 
         :class="['grid-cols-1', 'md:grid-cols-[240px_1fr]', 'lg:grid-cols-[240px_1fr_320px]']">
      
      <!-- Left Sidebar (Desktop) -->
      <aside class="hidden md:flex flex-col border-r border-[var(--border-subtle)] bg-[var(--bg-panel)] h-full overflow-hidden">
        <nav class="flex-none p-4 space-y-1">
          <div class="text-[10px] font-bold text-[var(--fg-tertiary)] uppercase tracking-wider mb-4 px-3 py-2">Modules</div>
          <RouterLink v-for="link in links" :key="link.path" :to="link.path" 
            class="group flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-[var(--fg-secondary)] hover:text-white hover:bg-[var(--bg-hover)] transition-all duration-200 border border-transparent"
            active-class="bg-[var(--accent-surface)] text-[var(--accent-primary)] border-[var(--accent-primary)]/20 shadow-sm shadow-[var(--accent-glow)]"
          >
            <Icon :name="link.icon" size="18" class="opacity-70 group-hover:opacity-100 group-hover:scale-110 transition-all duration-200" />
            {{ link.name }}
          </RouterLink>
        </nav>
        
        <!-- Session List -->
        <div class="flex-1 min-h-0 border-t border-[var(--border-subtle)] flex flex-col">
            <SessionList @select="handleSessionSelect" />
        </div>

        <div class="p-4 border-t border-[var(--border-subtle)] bg-[var(--bg-surface)]/30 shrink-0">
          <div class="flex items-center justify-between text-xs text-[var(--fg-tertiary)]">
            <span>v0.1.0 Beta</span>
            <div class="flex gap-2">
              <button class="hover:text-white transition-colors"><Icon name="settings" size="14" /></button>
            </div>
          </div>
        </div>
      </aside>

      <!-- Center Content -->
      <main class="flex flex-col min-w-0 overflow-hidden relative bg-[var(--bg-app)] h-full">
        <div class="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-[var(--accent-surface)]/20 via-transparent to-transparent pointer-events-none"></div>
        <slot />
      </main>

      <!-- Right Panel (Desktop) -->
      <aside class="hidden lg:flex flex-col border-l border-[var(--border-subtle)] bg-[var(--bg-panel)] w-[320px] shadow-xl z-10 h-full overflow-hidden">
        <slot name="right" />
      </aside>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import Icon from '../components/common/Icon.vue'
import SessionList from '../components/chat/SessionList.vue'
import { sessionStore } from '../store'

const router = useRouter()
const mobileMenuOpen = ref(false)

const links = [
  { name: '对话 Chat', path: '/', icon: 'message-square' },
  { name: '计划 Plan Graph', path: '/plan', icon: 'git-merge' },
  { name: '知识库 Knowledge', path: '/kb', icon: 'database' },
  { name: '技能 Skills', path: '/skills', icon: 'tool' },
  { name: '提示词 Prompts', path: '/prompts', icon: 'terminal' },
  { name: '配置Config', path: '/config', icon: 'settings' },
]

function handleSessionSelect(sid: string) {
  sessionStore.setSessionId(sid)
  router.push('/')
}
</script>

<style scoped>
/* Scrollbar Styling */
::-webkit-scrollbar {
  width: 5px;
  height: 5px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: var(--bg-hover);
  border-radius: 10px;
}
::-webkit-scrollbar-thumb:hover {
  background: var(--fg-tertiary);
}
</style>
