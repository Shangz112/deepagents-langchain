import { Request, Response } from 'express'
import fetch from 'node-fetch'

interface StreamState {
  sessionId: string
  controller: AbortController
  buffer: string[] // Raw SSE chunks
  content: string // Accumulated text content
  status: 'generating' | 'completed' | 'error'
  subscribers: Response[]
  lastUpdate: number
  error?: string
}

// Track active streams
export const activeStreams = new Map<string, StreamState>()

const STREAM_TTL = 60 * 1000 // Keep finished stream state for 1 minute

export function getStreamStatus(sessionId: string) {
  const state = activeStreams.get(sessionId)
  if (!state) return null
  return {
    status: state.status,
    content: state.content,
    error: state.error
  }
}

export function abortSessionStream(sessionId: string): boolean {
  const state = activeStreams.get(sessionId)
  if (state) {
    state.controller.abort()
    state.status = 'error' // Or 'aborted'
    state.error = 'Aborted by user'
    notifySubscribers(state)
    cleanupStream(sessionId)
    return true
  }
  return false
}

function cleanupStream(sessionId: string, delay = 0) {
  setTimeout(() => {
    const state = activeStreams.get(sessionId)
    if (state && state.subscribers.length === 0 && state.status !== 'generating') {
        activeStreams.delete(sessionId)
    }
  }, delay)
}

function notifySubscribers(state: StreamState, chunk?: string) {
    const dead: Response[] = []
    state.subscribers.forEach(res => {
        if (res.writableEnded) {
            dead.push(res)
            return
        }
        if (chunk) {
            res.write(chunk)
        } else if (state.status === 'completed' || state.status === 'error') {
            res.end()
        }
    })
    
    // Remove dead subscribers
    if (dead.length > 0) {
        state.subscribers = state.subscribers.filter(s => !dead.includes(s))
    }
}

export async function proxySSE(req: Request, res: Response, target: string, sessionId?: string) {
  if (!sessionId) {
      // Fallback for non-session streams (if any)
      return proxyDirect(req, res, target)
  }

  let state = activeStreams.get(sessionId)
  
  // Set headers
  res.setHeader('Content-Type', 'text/event-stream')
  res.setHeader('Cache-Control', 'no-cache')
  res.setHeader('Connection', 'keep-alive')
  res.setHeader('X-Accel-Buffering', 'no')

  if (state && state.status === 'generating') {
      // Join existing stream
      console.log(`[SSE] Joining existing stream for ${sessionId}`)
      state.subscribers.push(res)
      
      // Replay history
      for (const chunk of state.buffer) {
          res.write(chunk)
      }
      
      // Handle client disconnect
      req.on('close', () => {
          if (state) {
              state.subscribers = state.subscribers.filter(s => s !== res)
          }
      })
      return
  }

  // Start new stream
  console.log(`[SSE] Starting new stream for ${sessionId}`)
  const controller = new AbortController()
  state = {
      sessionId,
      controller,
      buffer: [],
      content: '',
      status: 'generating',
      subscribers: [res],
      lastUpdate: Date.now()
  }
  activeStreams.set(sessionId, state)

  req.on('close', () => {
      if (state) {
          state.subscribers = state.subscribers.filter(s => s !== res)
          // We DO NOT abort the controller here, to allow background generation
          // But if no subscribers left? We still keep it running until upstream finishes
      }
  })

  try {
    const r = await fetch(target, { 
      signal: controller.signal,
      timeout: 0, 
      headers: { 'Accept': 'text/event-stream' }
    } as any)

    if (!r.ok) {
       throw new Error(`Upstream error: ${r.status}`)
    }
    
    if (!r.body) {
        res.end()
        activeStreams.delete(sessionId)
        return
    }

    r.body.on('data', (chunk: Buffer) => {
        const chunkStr = chunk.toString()
        if (state) {
            state.buffer.push(chunkStr)
            state.lastUpdate = Date.now()
            
            // Extract content for status query
            // Simple parsing: look for "content": "..."
            try {
                // chunkStr might contain multiple lines "data: ...\n\n"
                const lines = chunkStr.split('\n')
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const jsonStr = line.slice(6).trim()
                        if (jsonStr === '[DONE]') continue
                        try {
                            const data = JSON.parse(jsonStr)
                            if (data.content) {
                                state.content += data.content
                            } else if (data.type === 'reasoning' && data.content) {
                                // Optionally store reasoning? User asked for "generated content".
                                // Usually main content is what matters for "recovery".
                            }
                        } catch (e) {
                            // ignore partial JSON
                        }
                    }
                }
            } catch (e) {
                // ignore
            }
            
            notifySubscribers(state, chunkStr)
        }
    })

    r.body.on('end', () => {
        if (state) {
            state.status = 'completed'
            notifySubscribers(state)
            cleanupStream(sessionId, STREAM_TTL)
        }
    })

    r.body.on('error', (e: Error) => {
        if (state) {
            state.status = 'error'
            state.error = e.message
            notifySubscribers(state)
            activeStreams.delete(sessionId)
        }
    })

  } catch (e: any) {
      if (state) {
          state.status = 'error'
          state.error = e.message
          notifySubscribers(state)
          activeStreams.delete(sessionId)
      }
      if (!res.writableEnded) {
          res.status(502).end()
      }
  }
}

async function proxyDirect(req: Request, res: Response, target: string) {
    // Fallback logic for simple proxy without state tracking
    const controller = new AbortController()
    req.on('close', () => controller.abort())
    try {
        const r = await fetch(target, { 
            signal: controller.signal,
            timeout: 0,
            headers: { 'Accept': 'text/event-stream' }
        } as any)
        
        res.setHeader('Content-Type', 'text/event-stream')
        res.setHeader('Cache-Control', 'no-cache')
        res.setHeader('Connection', 'keep-alive')
        
        if (r.body) {
            r.body.pipe(res)
        } else {
            res.end()
        }
    } catch (e) {
        if (!res.writableEnded) res.end()
    }
}
