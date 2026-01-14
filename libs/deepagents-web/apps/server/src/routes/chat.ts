import { Router } from 'express'
import { createSession, getSession, deleteSession, sendMessage, streamSession, getPrompts, getSessionConfig, updateSessionConfig, getSessionContext } from '../pythonClient'
import { proxySSE } from '../sse'
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
router.get('/sessions/:id', async (req, res) => {
  try {
    const s = await getSession(req.params.id)
    res.json(s)
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
router.post('/sessions/:id/messages', async (req, res) => {
  try {
    const r = await sendMessage(req.params.id, req.body.content, req.body.tools)
    res.json(r)
  } catch (e: any) {
    res.status(502).json({ error: 'python_service_unavailable', detail: String(e?.message || e) })
  }
})
router.get('/sessions/:id/stream', async (req, res) => {
  try {
    const url = streamSession(req.params.id)
    await proxySSE(req, res, url)
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