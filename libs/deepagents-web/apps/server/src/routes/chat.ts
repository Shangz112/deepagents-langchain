import { Router } from 'express'
import { createSession, listSessions, getSession, deleteSession, deleteSessionsBatch, updateSessionMeta, exportSession, sendMessage, streamSession, getPrompts, getSessionConfig, updateSessionConfig, getSessionContext } from '../pythonClient'
import { proxySSE, abortSessionStream, getStreamStatus } from '../sse'
const router = Router()
router.get('/prompts', async (req, res) => {
  try {
    const p = await getPrompts()
    res.json(p)
  } catch (e: any) {
    res.status(502).json({ error: 'python_service_unavailable', detail: String(e?.message || e) })
  }
})
router.post('/sessions', async (req, res) => {
  try {
    const s = await createSession()
    res.json(s)
  } catch (e: any) {
    res.status(502).json({ error: 'python_service_unavailable', detail: String(e?.message || e) })
  }
})
router.get('/sessions', async (req, res) => {
  try {
    const s = await listSessions()
    res.json(s)
  } catch (e: any) {
    res.status(502).json({ error: 'python_service_unavailable', detail: String(e?.message || e) })
  }
})
router.get('/sessions/:id', async (req, res) => {
  try {
    const s = await getSession(req.params.id)
    res.json(s)
  } catch (e: any) {
    res.status(502).json({ error: 'python_service_unavailable', detail: String(e?.message || e) })
  }
})
router.delete('/sessions/batch', async (req, res) => {
  try {
    const ids = req.body.ids
    const r = await deleteSessionsBatch(ids)
    res.json(r)
  } catch (e: any) {
    res.status(502).json({ error: 'python_service_unavailable', detail: String(e?.message || e) })
  }
})
router.delete('/sessions/:id', async (req, res) => {
  try {
    const r = await deleteSession(req.params.id)
    res.json(r)
  } catch (e: any) {
    res.status(502).json({ error: 'python_service_unavailable', detail: String(e?.message || e) })
  }
})
router.put('/sessions/:id', async (req, res) => {
  try {
    const r = await updateSessionMeta(req.params.id, req.body)
    res.json(r)
  } catch (e: any) {
    res.status(502).json({ error: 'python_service_unavailable', detail: String(e?.message || e) })
  }
})
router.get('/sessions/:id/export', async (req, res) => {
  try {
    const r = await exportSession(req.params.id)
    res.json(r)
  } catch (e: any) {
    res.status(502).json({ error: 'python_service_unavailable', detail: String(e?.message || e) })
  }
})
router.get('/sessions/:id/config', async (req, res) => {
  try {
    const r = await getSessionConfig(req.params.id)
    res.json(r)
  } catch (e: any) {
    res.status(502).json({ error: 'python_service_unavailable', detail: String(e?.message || e) })
  }
})
router.post('/sessions/:id/config', async (req, res) => {
  try {
    const r = await updateSessionConfig(req.params.id, req.body)
    res.json(r)
  } catch (e: any) {
    res.status(502).json({ error: 'python_service_unavailable', detail: String(e?.message || e) })
  }
})
router.get('/sessions/:id/context', async (req, res) => {
  try {
    const r = await getSessionContext(req.params.id)
    res.json(r)
  } catch (e: any) {
    res.status(502).json({ error: 'python_service_unavailable', detail: String(e?.message || e) })
  }
})
router.get('/sessions/:id/status', (req, res) => {
  const status = getStreamStatus(req.params.id)
  if (status) {
    res.json(status)
  } else {
    // If no stream is active, we assume it's idle or completed.
    // We can return a default "idle" status.
    res.json({ status: 'idle' })
  }
})

router.post('/sessions/:id/messages', async (req, res) => {
  try {
    const r = await sendMessage(req.params.id, req.body.content, req.body.tools)
    res.json(r)
  } catch (e: any) {
    res.status(502).json({ error: 'python_service_unavailable', detail: String(e?.message || e) })
  }
})
router.post('/sessions/:id/abort', async (req, res) => {
  try {
    const aborted = abortSessionStream(req.params.id)
    res.json({ aborted })
  } catch (e: any) {
    res.status(500).json({ error: 'abort_failed', detail: String(e?.message || e) })
  }
})
router.get('/sessions/:id/stream', async (req, res) => {
  try {
    const url = streamSession(req.params.id)
    await proxySSE(req, res, url, req.params.id)
  } catch (e: any) {
    if (!res.headersSent) {
      res.status(502).json({ error: 'python_service_unavailable', detail: String(e?.message || e) })
    } else {
      console.error('Error during SSE proxy:', e)
      res.end()
    }
  }
})
export default router