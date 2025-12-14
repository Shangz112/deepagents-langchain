import { Router } from 'express'
const router = Router()
let subagents: any[] = []
router.get('/subagents', (req: any, res: any) => { res.json(subagents) })
router.post('/subagents', (req: any, res: any) => { const a = req.body; subagents = [...subagents, a]; res.status(201).json(a) })
router.delete('/subagents', (req: any, res: any) => { subagents = []; res.status(204).end() })
router.get('/plan/graph', (req: any, res: any) => { res.json({ nodes: [], edges: [] }) })
export default router