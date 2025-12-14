import { Router } from 'express'
import { listSkills } from '../pythonClient'
const router = Router()
router.get('/', async (req, res) => { const skills = await listSkills(); res.json(skills) })
export default router