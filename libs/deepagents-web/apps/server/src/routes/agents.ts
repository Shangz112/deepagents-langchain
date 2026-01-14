import { Router } from 'express'
import { getSubAgents, saveSubAgent, clearSubAgents } from '../pythonClient'

const router = Router()

router.get('/subagents', async (req, res) => {
  try {
    const agents = await getSubAgents()
    res.json(agents)
  } catch (e: any) {
    res.status(502).json({ error: 'python_service_unavailable', detail: e.message })
  }
})

router.post('/subagents', async (req, res) => {
  try {
    const a = await saveSubAgent(req.body)
    res.status(201).json(a)
  } catch (e: any) {
    res.status(502).json({ error: 'python_service_unavailable', detail: e.message })
  }
})

router.delete('/subagents', async (req, res) => {
  try {
    await clearSubAgents()
    res.status(204).send()
  } catch (e: any) {
    res.status(502).json({ error: 'python_service_unavailable', detail: e.message })
  }
})
router.get('/plan/graph', (req: any, res: any) => { res.json({ nodes: [], edges: [] }) })
export default router