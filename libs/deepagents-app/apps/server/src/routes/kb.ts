import { Router } from 'express'
const router = Router()
let sources: any[] = []
router.get('/sources', (req, res) => { res.json(sources) })
router.post('/sources', (req, res) => { const s = req.body; sources = [...sources, s]; res.status(201).json(s) })
router.delete('/sources/:id', (req, res) => { sources = sources.filter(x => String(x.id) !== req.params.id); res.status(204).end() })
router.get('/query', (req, res) => { res.json({ records: [] }) })
router.post('/update', (req, res) => { res.json({ ok: true }) })
export default router