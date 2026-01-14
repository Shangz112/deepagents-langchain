import { Router } from 'express'
import { saveFeedback, exportFeedback } from '../pythonClient'

const router = Router()

router.post('/', async (req, res) => {
  try {
    const r = await saveFeedback(req.body)
    res.json(r)
  } catch (e: any) {
    res.status(502).json({ error: 'python_service_unavailable', detail: String(e?.message || e) })
  }
})

router.get('/export', async (req, res) => {
  try {
    const r = await exportFeedback()
    res.json(r)
  } catch (e: any) {
    res.status(502).json({ error: 'python_service_unavailable', detail: String(e?.message || e) })
  }
})

export default router
