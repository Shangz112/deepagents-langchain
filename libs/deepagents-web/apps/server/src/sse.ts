import { Request, Response } from 'express'
import fetch from 'node-fetch'

export async function proxySSE(req: Request, res: Response, target: string) {
  const controller = new AbortController()
  
  // Handle client disconnect
  const closeHandler = () => controller.abort()
  req.on('close', closeHandler)

  try {
    const r = await fetch(target, { 
      signal: controller.signal,
      timeout: 0, // Disable timeout for SSE
      headers: {
        'Accept': 'text/event-stream'
      }
    } as any)

    if (!r.ok) {
      console.error(`SSE upstream error: ${r.status} ${r.statusText}`)
      if (!res.headersSent) {
        res.status(r.status).end()
      }
      return
    }

    res.setHeader('Content-Type', 'text/event-stream')
    res.setHeader('Cache-Control', 'no-cache')
    res.setHeader('Connection', 'keep-alive')
    res.setHeader('X-Accel-Buffering', 'no') // Nginx buffering off

    if (!r.body) {
      res.end()
      return
    }

    // Manual stream handling for better control and debugging
    r.body.on('data', (chunk: Buffer) => {
      if (!res.writableEnded) {
        res.write(chunk)
      }
    })

    r.body.on('end', () => {
      if (!res.writableEnded) {
        res.end()
      }
    })

    r.body.on('error', (e: Error) => {
      console.error('SSE stream error:', e)
      if (!res.writableEnded) {
        res.end()
      }
    })

  } catch (e: any) {
    if (e.name === 'AbortError') {
      return
    }
    console.error('SSE Proxy exception:', e)
    throw e 
  } finally {
    req.off('close', closeHandler)
  }
}