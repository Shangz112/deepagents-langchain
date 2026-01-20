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

export interface SessionTask {
  id: string
  type: 'generation' | 'tool_execution'
  status: 'pending' | 'processing' | 'completed' | 'failed'
  priority: 'high' | 'low'
  timestamp: number
}

export interface SessionState {
  generating: boolean
  lastActive: number
  taskQueue: SessionTask[]
  contentBuffer: string
}

export const sessionManager = reactive({
  activeSessionId: null as string | null,
  sessionStates: new Map<string, SessionState>(),
  _statusTimer: null as any,
  
  init() {
    if (this._statusTimer) clearInterval(this._statusTimer)
    this._statusTimer = setInterval(() => {
      this.checkGlobalStatus()
    }, 200)
  },

  getState(sessionId: string): SessionState {
    if (!this.sessionStates.has(sessionId)) {
      this.sessionStates.set(sessionId, {
        generating: false,
        lastActive: Date.now(),
        taskQueue: [],
        contentBuffer: ''
      })
    }
    return this.sessionStates.get(sessionId)!
  },

  updateState(sessionId: string, updates: Partial<SessionState>) {
    const state = this.getState(sessionId)
    Object.assign(state, updates)
    state.lastActive = Date.now()
  },

  addTask(sessionId: string, task: SessionTask) {
    const state = this.getState(sessionId)
    state.taskQueue.push(task)
    state.lastActive = Date.now()
  },

  completeTask(sessionId: string, taskId: string) {
    const state = this.getState(sessionId)
    const idx = state.taskQueue.findIndex(t => t.id === taskId)
    if (idx !== -1) {
      state.taskQueue.splice(idx, 1)
    }
    state.lastActive = Date.now()
  },

  checkGlobalStatus() {
    const now = Date.now()
    // Requirement 6: Timeout handling (>30min inactive)
    for (const [sid, state] of this.sessionStates.entries()) {
      if (now - state.lastActive > 30 * 60 * 1000) {
         if (!state.generating && state.taskQueue.length === 0) {
             // Clean up resources for inactive session
             state.contentBuffer = '' 
         }
      }
    }
  },
  
  // Requirement 6: Force Reset
  resetSessionState(sessionId: string) {
      const state = this.getState(sessionId)
      state.generating = false
      state.taskQueue = []
      state.contentBuffer = ''
      state.lastActive = Date.now()
      
      // Also reset chatStore if it matches
      if (chatStore.streamingSessionId === sessionId) {
          chatStore.closeStream()
      }
  }
})

// Initialize immediately
sessionManager.init()

export const sessionStore = reactive({
  sessionId: null as string | null,
  sessions: [] as any[],
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
    // Requirement 3: Session Switching Flow
    // 1. Trigger sessionWillChange (implicit by updating activeSessionId)
    sessionManager.activeSessionId = id
    this.sessionId = id
    
    // 2. Save current session state (handled by sessionManager updates during stream)
    
    // 3. Load new session state is handled by the component watching sessionId or checkSessionStatus called by View
  },
  async loadSessions() {
    try {
        const res = await axios.get('/api/v1/chat/sessions')
        if (Array.isArray(res.data)) {
            this.sessions = res.data
        } else {
            console.warn('Expected array for sessions but got:', res.data)
            this.sessions = []
        }
    } catch (e) {
        console.error('Failed to load sessions', e)
        this.sessions = []
    }
  },
  async createSession(message: string = 'New Session') {
      try {
          const res = await axios.post('/api/v1/chat/sessions', { message })
          await this.loadSessions()
          return res.data.id
      } catch (e) {
          console.error('Failed to create session', e)
          throw e
      }
  },
  async deleteSession(id: string) {
      try {
          await axios.delete(`/api/v1/chat/sessions/${id}`)
          this.sessions = this.sessions.filter(s => s.id !== id)
          if (this.sessionId === id) {
              this.sessionId = null
              chatStore.messages = []
              this.logs = []
          }
      } catch (e) {
          console.error('Failed to delete session', e)
      }
  },
  async deleteSessions(ids: string[]) {
      try {
          await axios.delete('/api/v1/chat/sessions/batch', { data: { ids } })
          const idSet = new Set(ids)
          this.sessions = this.sessions.filter(s => !idSet.has(s.id))
          if (this.sessionId && idSet.has(this.sessionId)) {
              this.sessionId = null
              chatStore.messages = []
              this.logs = []
          }
      } catch (e) {
          console.error('Failed to delete sessions', e)
      }
  },
  async renameSession(id: string, name: string) {
      try {
          await axios.put(`/api/v1/chat/sessions/${id}`, { name })
          const sess = this.sessions.find(s => s.id === id)
          if (sess) sess.name = name
      } catch (e) {
          console.error('Failed to rename session', e)
      }
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
  get isStreaming() {
      if (!sessionStore.sessionId) return false
      return sessionManager.getState(sessionStore.sessionId).generating
  },
  streamingSessionId: null as string | null,
  eventSource: null as EventSource | null,
  
  // Requirement 2: Background task tracking
  generatingTaskId: null as string | null,
  currentSessionId: null as string | null,

  closeStream() {
    if (this.eventSource) {
      this.eventSource.close()
      this.eventSource = null
    }
    // this.isStreaming is computed
    
    // Update SessionManager
    if (this.streamingSessionId) {
        sessionManager.updateState(this.streamingSessionId, { generating: false })
        if (this.generatingTaskId) {
            sessionManager.completeTask(this.streamingSessionId, this.generatingTaskId)
        }
    }

    this.streamingSessionId = null
    this.generatingTaskId = null
  },

  // Requirement 3: Abort API
  async abortGeneration() {
    const sid = this.streamingSessionId
    this.closeStream()
    if (sid) {
        try {
            await axios.post(`/api/v1/chat/sessions/${sid}/abort`)
        } catch (e) {
            console.error('Failed to abort session on server', e)
        }
    }
  },

  async checkSessionStatus(sessionId: string) {
    try {
        const res = await axios.get(`/api/v1/chat/sessions/${sessionId}/status`, {
            headers: { 'X-Interaction-Type': 'passive' }
        })
        const status = res.data
        
        if (status.status === 'generating') {
            console.log('Session is generating, reconnecting...', sessionId)
            
            // Update SessionManager
            sessionManager.updateState(sessionId, { generating: true })
            
            // If we are reconnecting, the stream will replay the entire generation history.
            // We need to ensure we don't have partial stale content.
            // Check if the last message is an assistant message.
            let lastMsg = this.messages[this.messages.length - 1]
            
            if (!lastMsg || lastMsg.role !== 'assistant') {
                const assistantMsgId = String(Date.now() + 1)
                lastMsg = reactive({
                    id: assistantMsgId,
                    role: 'assistant',
                    content: '',
                    reasoning: '',
                    timestamp: Date.now(),
                    streaming: true,
                    toolEvents: [],
                    isError: false
                })
                this.messages.push(lastMsg)
            } else {
                // Reset content as it will be replayed
                lastMsg.streaming = true
                lastMsg.content = '' 
                lastMsg.reasoning = ''
                lastMsg.toolEvents = []
            }
            
            this.connectToStream(sessionId, lastMsg)
        } else {
            // Ensure local state matches backend
            sessionManager.updateState(sessionId, { generating: false })
            // If we thought it was generating but backend says no, stop local stream
            if (this.streamingSessionId === sessionId) {
                this.closeStream()
            }
        }
    } catch (e) {
        console.error('Failed to check session status', e)
    }
  },

  async connectToStream(sessionId: string, assistantMsg: any) {
      this.closeStream()
      
      const es = new EventSource(`/api/v1/chat/sessions/${sessionId}/stream`)
      this.eventSource = es
      // this.isStreaming is computed
      this.streamingSessionId = sessionId
      this.generatingTaskId = String(Date.now())

      // Update SessionManager
      sessionManager.updateState(sessionId, { generating: true })
      sessionManager.addTask(sessionId, { 
          id: this.generatingTaskId, 
          type: 'generation', 
          status: 'processing', 
          priority: 'high', 
          timestamp: Date.now() 
      })
      
      es.onmessage = e => {
          try {
            const d = JSON.parse(e.data)
            
            if (d.type === 'ping') return

            if (d.type === 'reasoning') {
               assistantMsg.reasoning = (assistantMsg.reasoning || '') + (d.content || '')
            }
            
            if (d.type === 'message' || d.type === 'chunk') {
              assistantMsg.content += (d.content || '')
              // Sync content buffer
              sessionManager.updateState(sessionId, { contentBuffer: assistantMsg.content })
            }

            if (d.type === 'error') {
               assistantMsg.content += "\n\nError: " + (d.content || "Unknown error")
               assistantMsg.isError = true
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
                } else {
                     // Preserve existing content and mark as interrupted
                     assistantMsg.content += "\n\n[System: Connection interrupted]"
                     assistantMsg.isError = true
                }
            }
            this.closeStream()
         }
      }
  },

  async loadSessionHistory(sid: string) {
      try {
        const res = await axios.get(`/api/v1/chat/sessions/${sid}/context`)
        if (res.data && res.data.history) {
           // Reconstruct messages and tool events
           const messages: any[] = []
           const toolOutputs: Record<string, any> = {}
           
           // First pass: index tool outputs
           res.data.history.forEach((m: any) => {
             if (m.role === 'tool' && m.tool_call_id) {
               toolOutputs[m.tool_call_id] = m
             }
           })
    
           // Second pass: build messages
           res.data.history.forEach((m: any, idx: number) => {
             // Skip tool messages as they are folded into assistant messages
             if (m.role === 'tool') return
    
             const msg: any = {
               id: `${sid}-${idx}`,
               role: m.role,
               content: m.content,
               // Requirement 1: Restore metadata
               timestamp: m.timestamp || Date.now(),
               reasoning: m.reasoning || (m.metadata?.reasoning) || '',
               toolEvents: []
             }
    
             if (m.role === 'assistant' && m.tool_calls) {
               msg.toolEvents = m.tool_calls.map((tc: any) => {
                 const outputMsg = toolOutputs[tc.id]
                 return {
                   id: tc.id,
                   name: tc.name,
                   status: outputMsg ? 'completed' : 'in_progress',
                   input: tc.args,
                   output: outputMsg ? outputMsg.content : undefined,
                   timestamp: m.timestamp || Date.now()
                 }
               })
             }
             
             messages.push(msg)
           })
           
           this.messages = messages
           this.currentSessionId = sid
        } else {
           this.messages = []
           this.currentSessionId = sid
        }
      } catch (e: any) {
        console.error('Failed to load history', e)
        this.messages = []
        if (e.response && e.response.status === 404) {
             sessionStore.sessionId = null
             this.currentSessionId = null
        }
      }
  },

  async sendMessage(payload: { text: string; tools: boolean }, sessionId: string) {
      this.currentSessionId = sessionId
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

        // Check if we need to reload sessions (for auto-rename)
        const sessionsList = Array.isArray(sessionStore.sessions) ? sessionStore.sessions : []
        if (sessionsList.length > 0) {
            const currentSession = sessionsList.find((s: any) => s.id === sessionId)
            if (currentSession && (currentSession.name === 'New Session' || currentSession.name === `Session ${sessionId}`)) {
                setTimeout(() => sessionStore.loadSessions(), 500)
            }
        }

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

        // Connect to stream
        this.connectToStream(sessionId, assistantMsg)

      } catch (e) {
        console.error('Send failed', e)
        this.messages.push({
          id: String(Date.now()),
          role: 'system',
          content: 'Error sending message: ' + (e as Error).message,
          timestamp: Date.now()
        })
        // this.isStreaming is computed
      }
  }
})
