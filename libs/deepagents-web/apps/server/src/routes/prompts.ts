import { Router } from 'express'
import { getPrompts, savePrompts, getQuickStarters, saveQuickStarters } from '../pythonClient'

const router = Router()

router.get('/quick-starters', async (req, res) => {
    try {
        const data = await getQuickStarters()
        res.json(data)
    } catch (e: any) {
        res.status(502).json({ error: 'python_service_unavailable', detail: e.message })
    }
})

router.post('/quick-starters', async (req, res) => {
    try {
        const data = await saveQuickStarters(req.body)
        res.json(data)
    } catch (e: any) {
        res.status(502).json({ error: 'python_service_unavailable', detail: e.message })
    }
})

router.get('/templates', async (req, res) => {
  try {
    const prompts = await getPrompts()
    // Map Python prompts to templates with versions
    const templates = prompts.map((p: any) => ({
      ...p,
      versions: [{ version: p.version || 1, content: p.content, updated: p.updated || new Date().toISOString() }]
    }))
    res.json(templates)
  } catch (e: any) {
    res.status(502).json({ error: 'python_service_unavailable', detail: e.message })
  }
})

router.post('/templates', async (req, res) => {
  try {
    const t = req.body
    const prompts = await getPrompts()
    // Add new prompt
    const newPrompt = {
      id: t.id || Date.now().toString(),
      name: t.name,
      desc: t.desc,
      content: t.content,
      version: '1.0',
      updated: new Date().toISOString()
    }
    prompts.push(newPrompt)
    await savePrompts(prompts)
    res.status(201).json({ ...newPrompt, versions: [{ version: 1, content: newPrompt.content }] })
  } catch (e: any) {
    res.status(502).json({ error: 'python_service_unavailable', detail: e.message })
  }
})

router.get('/templates/:id/versions', async (req, res) => {
    // Return single version from current prompt
    try {
        const prompts = await getPrompts()
        const p = prompts.find((x: any) => String(x.id) === req.params.id)
        if (p) {
            res.json([{ version: p.version || 1, content: p.content, updated: p.updated }])
        } else {
            res.json([])
        }
    } catch (e: any) {
        res.status(502).json({ error: 'python_service_unavailable', detail: e.message })
    }
})

router.post('/templates/:id/versions', async (req, res) => {
    // Update the prompt content (effectively "new version" becomes "current version")
    try {
        const prompts = await getPrompts()
        const idx = prompts.findIndex((x: any) => String(x.id) === req.params.id)
        if (idx >= 0) {
            prompts[idx].content = req.body.content
            prompts[idx].updated = new Date().toISOString()
            prompts[idx].version = String((parseFloat(prompts[idx].version) || 1) + 0.1)
            await savePrompts(prompts)
            res.status(201).json({ version: prompts[idx].version, content: prompts[idx].content })
        } else {
            res.status(404).json({ error: 'not_found' })
        }
    } catch (e: any) {
        res.status(502).json({ error: 'python_service_unavailable', detail: e.message })
    }
})

router.post('/templates/:id/preview', (req, res) => {
    // Simple interpolation
    const content = String(req.body.content || '')
    const vars = req.body.variables || {}
    const result = content.replace(/\{\{(\w+)\}\}/g, (_, k) => vars[k] ?? '')
    res.json({ content: result })
})

export default router