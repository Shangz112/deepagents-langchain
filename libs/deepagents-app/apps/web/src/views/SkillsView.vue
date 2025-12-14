<template>
  <div class="h-full flex flex-col overflow-hidden bg-[var(--bg-app)]">
    <!-- Header -->
    <header class="flex-none p-6 border-b border-[var(--border-subtle)] bg-[var(--bg-panel)]/80 backdrop-blur-md">
      <div class="flex justify-between items-center">
        <div>
          <h1 class="text-2xl font-bold text-[var(--fg-primary)] tracking-tight flex items-center gap-3">
            <Icon name="zap" size="28" class="text-[var(--accent-primary)]" />
            Skills Marketplace
          </h1>
          <p class="text-[var(--fg-secondary)] text-sm mt-1">Enable capabilities for your agents</p>
        </div>
        <div class="relative group">
           <input v-model="searchQuery" type="text" class="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-lg px-4 py-2 pl-10 text-sm text-[var(--fg-primary)] focus:border-[var(--accent-primary)] outline-none w-64 transition-all shadow-sm" placeholder="Search skills..." />
           <Icon name="search" size="16" class="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--fg-tertiary)] group-focus-within:text-[var(--accent-primary)] transition-colors" />
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="flex-1 overflow-y-auto p-6 relative">
      <!-- Background Decor -->
      <div class="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
         <div class="absolute top-[20%] right-[10%] w-96 h-96 bg-[var(--accent-primary)]/5 rounded-full blur-3xl"></div>
      </div>

      <div class="max-w-7xl mx-auto relative z-10">
        
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          <div v-for="skill in filteredSkills" :key="skill.id" 
               class="panel-card p-5 relative overflow-hidden group hover:-translate-y-1 transition-all duration-300 shadow-sm hover:shadow-lg hover:shadow-[var(--accent-glow)]/10 border-transparent hover:border-[var(--accent-primary)]/30"
               :class="skill.enabled ? 'bg-[var(--bg-panel)]' : 'bg-[var(--bg-app)] opacity-90'">
            
            <!-- Active Indicator (Corner Ribbon) -->
            <div v-if="skill.enabled" class="absolute top-0 right-0 w-16 h-16 overflow-hidden">
              <div class="absolute top-0 right-0 transform translate-x-1/2 -translate-y-1/2 rotate-45 bg-[var(--accent-primary)] w-16 h-4 shadow-sm"></div>
            </div>

            <div class="flex justify-between items-start mb-4">
              <div class="p-3 rounded-xl transition-colors duration-300"
                   :class="skill.enabled ? 'bg-[var(--accent-surface)] text-[var(--accent-primary)]' : 'bg-[var(--bg-surface)] text-[var(--fg-tertiary)] group-hover:text-[var(--fg-primary)]'">
                <Icon :name="skill.icon" size="24" />
              </div>
              
              <!-- Toggle Switch -->
              <label class="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" v-model="skill.enabled" class="sr-only peer">
                <div class="w-10 h-5 bg-[var(--bg-surface)] border border-[var(--border-subtle)] peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-[var(--fg-secondary)] after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-[var(--accent-primary)] peer-checked:after:bg-white"></div>
              </label>
            </div>
            
            <h3 class="font-bold text-[var(--fg-primary)] mb-1 group-hover:text-[var(--accent-primary)] transition-colors">{{ skill.name }}</h3>
            <p class="text-[var(--fg-secondary)] text-sm h-10 line-clamp-2 mb-4 leading-relaxed">{{ skill.description }}</p>
            
            <div class="flex items-center justify-between text-xs text-[var(--fg-tertiary)] border-t border-[var(--border-subtle)] pt-3 mt-auto">
              <div class="flex items-center gap-1.5">
                <span class="uppercase tracking-wider font-semibold bg-[var(--bg-surface)] px-1.5 py-0.5 rounded text-[10px]">{{ skill.source }}</span>
                <span v-if="skill.override" class="text-[var(--warning)]" title="Overrides User Level">
                  <Icon name="alert-circle" size="12" />
                </span>
              </div>
              <div class="font-mono opacity-70">{{ skill.size }}</div>
            </div>

          </div>
        </div>

      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import Icon from '../components/common/Icon.vue'

interface Skill {
  id: string;
  name: string;
  description: string;
  icon: string;
  enabled: boolean;
  source: 'system' | 'user' | 'project';
  size: string;
  override?: boolean;
}

const searchQuery = ref('')
const skills = ref<Skill[]>([
  { id: '1', name: 'Web Search', description: 'Search the internet for real-time information using Google or Bing.', icon: 'globe', enabled: true, source: 'system', size: '12KB' },
  { id: '2', name: 'Python Sandbox', description: 'Execute Python code for data analysis, plotting, and complex calculations.', icon: 'terminal', enabled: true, source: 'system', size: '45MB' },
  { id: '3', name: 'File System', description: 'Read and write files to the local workspace.', icon: 'folder', enabled: false, source: 'project', size: '8KB', override: true },
  { id: '4', name: 'Image Gen', description: 'Generate images from text descriptions using DALL-E or Stable Diffusion.', icon: 'image', enabled: false, source: 'user', size: '2KB' },
  { id: '5', name: 'Email Client', description: 'Send and receive emails via SMTP/IMAP.', icon: 'mail', enabled: false, source: 'user', size: '15KB' },
  { id: '6', name: 'Git Integration', description: 'Clone repositories and manage version control.', icon: 'git-branch', enabled: true, source: 'project', size: '22KB' },
  { id: '7', name: 'Calendar', description: 'Manage schedules and set reminders.', icon: 'calendar', enabled: false, source: 'system', size: '10KB' },
  { id: '8', name: 'Weather', description: 'Get current weather forecasts for any location.', icon: 'cloud-rain', enabled: true, source: 'system', size: '5KB' }
])

const filteredSkills = computed(() => {
  if (!searchQuery.value) return skills.value
  return skills.value.filter(s => 
    s.name.toLowerCase().includes(searchQuery.value.toLowerCase()) || 
    s.description.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
})

const load = async () => {
  try {
    const r = await axios.get('/api/v1/skills')
    // Merge with mock data for demo purposes if API returns empty or simple list
    if (Array.isArray(r.data) && r.data.length > 0) {
      // Map real data to UI model if needed
      // skills.value = ...
    }
  } catch (e) {
    console.log('Using mock skills data')
  }
}

onMounted(() => {
  load()
})
</script>

<style scoped></style>
