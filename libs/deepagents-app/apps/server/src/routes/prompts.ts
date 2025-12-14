import { Router } from 'express'
const router = Router()
const templates: Record<string, any> = {}
router.get('/templates', (req, res) => { res.json(Object.values(templates)) })
router.post('/templates', (req, res) => { const t = req.body; templates[t.id] = { ...t, versions: [] }; res.status(201).json(templates[t.id]) })
router.get('/templates/:id/versions', (req, res) => { const t = templates[req.params.id] || { versions: [] }; res.json(t.versions) })
router.post('/templates/:id/versions', (req, res) => { const t = templates[req.params.id] || { versions: [] }; const v = { ...req.body, version: (t.versions?.length || 0) + 1 }; t.versions = [...(t.versions || []), v]; templates[req.params.id] = t; res.status(201).json(v) })
router.post('/templates/:id/preview', (req, res) => { const t = templates[req.params.id]; const vars = req.body.variables || {}; const content = String(req.body.content || '').replace(/\{\{(\w+)\}\}/g, (_, k) => vars[k] ?? ''); res.json({ content }) })
export default router