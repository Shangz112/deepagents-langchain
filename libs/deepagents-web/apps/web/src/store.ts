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

export const chatStore = reactive({
  messages: [] as any[],
  isStreaming: false,
  eventSource: null as EventSource | null,

  closeStream() {
    if (this.eventSource) {
      this.eventSource.close()
      this.eventSource = null
    }
    this.isStreaming = false
  },

  async sendMessage(payload: { text: string; tools: boolean }, sessionId: string) {
      // Add User Message
      const userMsgId = String(Date.now())
      this.messages.push({ 
        id: userMsgId, 
        role: 'user', 
        content: payload.text, 
        timestamp: Date.now() 
      })

      try {
        await axios.post(`/api/v1/chat/sessions/${sessionId}/messages`, { 
          content: payload.text, 
          tools: payload.tools 
        })

        // Start SSE
        this.closeStream()
        
        const es = new EventSource(`/api/v1/chat/sessions/${sessionId}/stream`)
        this.eventSource = es
        this.isStreaming = true
        
        // Create placeholder for assistant message
        const assistantMsgId = String(Date.now() + 1)
        const assistantMsg = reactive({
          id: assistantMsgId,
          role: 'assistant',
          content: '',
          reasoning: '',
          timestamp: Date.now(),
          streaming: true,
          toolEvents: [] as any[],
          isError: false
        })
        this.messages.push(assistantMsg)

        es.onmessage = e => {
          try {
            const d = JSON.parse(e.data)
            
            if (d.type === 'ping') return

            if (d.type === 'reasoning') {
               assistantMsg.reasoning = (assistantMsg.reasoning || '') + (d.content || '')
            }
            
            if (d.type === 'message' || d.type === 'chunk') {
              assistantMsg.content += (d.content || '')
            }
            
            if (d.type === 'tool') {
              const existingIdx = assistantMsg.toolEvents.findIndex((evt: any) => evt.id === d.id)
              if (existingIdx >= 0) {
                 if (d.input_chunk) {
                    const current = assistantMsg.toolEvents[existingIdx].input
                    if (typeof current === 'string') {
                        assistantMsg.toolEvents[existingIdx].input = current + d.input_chunk
                    } else {
                        assistantMsg.toolEvents[existingIdx].input = d.input_chunk
                    }
                 } else {
                    Object.assign(assistantMsg.toolEvents[existingIdx], d)
                 }
              } else {
                 assistantMsg.toolEvents.push({
                   id: d.id,
                   name: d.name,
                   status: d.status,
                   input: d.input || d.input_chunk || '',
                   output: d.output,
                   timestamp: Date.now()
                 })
              }
            }
            
            if (d.type === 'done') {
              assistantMsg.streaming = false
              this.closeStream()
            }
          } catch (err) {
            console.error('SSE Parse Error', err)
          }
        }
        
        es.onerror = (e) => {
           if (es.readyState === EventSource.CLOSED) {
              if (assistantMsg.streaming) {
                  console.warn('SSE Connection closed unexpectedly')
                  assistantMsg.streaming = false
                  if (!assistantMsg.content && !assistantMsg.reasoning) {
                       assistantMsg.content = "Error: Connection interrupted. Please try again."
                       assistantMsg.isError = true
                  }
              }
              this.closeStream()
           }
        }

      } catch (e) {
        console.error('Send failed', e)
        this.messages.push({
          id: String(Date.now()),
          role: 'system',
          content: 'Error sending message: ' + (e as Error).message,
          timestamp: Date.now()
        })
        this.isStreaming = false
      }
  }
})
