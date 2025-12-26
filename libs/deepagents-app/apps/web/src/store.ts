import { reactive, ref } from 'vue'
import axios from 'axios'

export const promptStore = reactive({
  prompts: [] as any[],
  async loadPrompts() {
    try {
      const res = await axios.get('/api/v1/chat/prompts')
      this.prompts = res.data
    } catch (e) {
      console.error('Failed to load prompts', e)
    }
  },
  async savePrompt(prompt: any) {
    try {
      const res = await axios.post('/api/v1/chat/prompts', prompt)
      if (prompt.id) {
         const idx = this.prompts.findIndex((p: any) => p.id === prompt.id)
         if (idx >= 0) Object.assign(this.prompts[idx], prompt)
      } else {
         prompt.id = res.data.id
         this.prompts.push(prompt)
      }
      await this.loadPrompts() // Reload to get updated timestamps
      return res.data.id
    } catch (e) {
      console.error('Failed to save prompt', e)
      throw e
    }
  },
  async deletePrompt(id: string) {
    try {
      await axios.delete(`/api/v1/chat/prompts/${id}`)
      this.prompts = this.prompts.filter((p: any) => p.id !== id)
    } catch (e) {
      console.error('Failed to delete prompt', e)
    }
  }
})

export const sessionStore = reactive({
  sessionId: null as string | null,
  config: {
    model: 'deepseek-ai/DeepSeek-V3.2',
    temperature: 0.7,
    middleware_enabled: true,
    system_prompt: undefined as string | undefined
  },
  logs: [] as any[],
  history: [] as any[],
  memorySummary: '',
  setSessionId(id: string) {
    this.sessionId = id
  },
  setConfig(cfg: any) {
    Object.assign(this.config, cfg)
  },
  addLog(log: any) {
    this.logs.push(log)
  },
  setHistory(hist: any[]) {
    this.history = hist
  },
  setSummary(sum: string) {
    this.memorySummary = sum
  }
})
