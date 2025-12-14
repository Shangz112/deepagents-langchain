import { Router } from 'express'
const router = Router()
router.post('/execute', async (req, res) => { res.json({ result: null }) })
export default router