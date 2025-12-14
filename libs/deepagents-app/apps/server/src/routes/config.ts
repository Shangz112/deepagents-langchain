import { Router } from 'express'
import { updateConfig, getConfig } from '../pythonClient'
const router = Router()
let config: any = { model: 'mock', middleware: [], backend: {} }
router.get('/', async (req, res) => { 
  try {
    const pyConfig: any = await getConfig()
    config.apiKey = pyConfig.api_key
    config.baseUrl = pyConfig.base_url
    config.modelName = pyConfig.model
    if (config.baseUrl?.includes('siliconflow')) {
        config.modelProvider = 'siliconflow'
    }
  } catch(e) {
    console.error("Error getting python config", e)
  }
  res.json(config) 
})
router.put('/', async (req, res) => { 
  config = req.body || {}; 
  try {
    await updateConfig(config)
  } catch(e) {
    console.error("Error updating python config", e)
  }
  res.json(config) 
})
router.get('/presets', (req, res) => { res.json([]) })
router.post('/presets', (req, res) => { res.status(201).json({}) })
router.delete('/presets', (req, res) => { res.status(204).end() })
router.post('/import', (req, res) => { res.json({ ok: true }) })
router.get('/export', (req, res) => { res.json(config) })
export default router