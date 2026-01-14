import { Router } from 'express'
import { listSkills } from '../pythonClient'

const router = Router()

router.get('/', async (req, res) => {
  try {
    const skills = await listSkills()
    res.json(skills)
  } catch (e: any) {
    res.status(502).json({ error: 'python_service_unavailable', detail: e.message })
  }
})

router.post('/execute', async (req, res) => {
  // Stub for tool execution - currently tools are executed by Python agent internally
  // If direct execution is needed, we need a new endpoint in Python
  res.json({ result: null })
})

export default router