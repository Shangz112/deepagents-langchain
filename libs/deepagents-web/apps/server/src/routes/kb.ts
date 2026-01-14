import { Router } from 'express'
import multer from 'multer'
import { getKBSources, saveKBSource, deleteKBSource, searchKnowledgeBase, uploadKBSource, renameKBSource, getKBSourcePreview, getKBSourceChunks, updateChunk } from '../pythonClient'
import fetch from 'node-fetch'

const router = Router()
const upload = multer({ storage: multer.memoryStorage() })

router.post('/upload', upload.single('file'), async (req, res) => {
  try {
    if (!req.file) return res.status(400).json({ error: 'No file uploaded' })
    
    // Fix Chinese filename encoding issue
    req.file.originalname = Buffer.from(req.file.originalname, 'latin1').toString('utf8')
    
    const template = req.body.template || 'default'
    const result = await uploadKBSource(req.file, template)
    res.json(result)
  } catch (e: any) {
    res.status(500).json({ error: e.message })
  }
})

router.get('/sources', async (req, res) => {
  try {
    const sources = await getKBSources()
    res.json(sources)
  } catch (e: any) {
    res.status(502).json({ error: 'python_service_unavailable', detail: e.message })
  }
})

router.post('/sources', async (req, res) => {
  try {
    const s = await saveKBSource(req.body)
    res.status(201).json(s)
  } catch (e: any) {
    res.status(502).json({ error: 'python_service_unavailable', detail: e.message })
  }
})

router.delete('/sources/:id', async (req, res) => {
  try {
    await deleteKBSource(req.params.id)
    res.status(204).send()
  } catch (e: any) {
    res.status(502).json({ error: 'python_service_unavailable', detail: e.message })
  }
})

router.put('/sources/:id', async (req, res) => {
  try {
    const { name } = req.body
    await renameKBSource(req.params.id, name)
    res.json({ ok: true })
  } catch (e: any) {
    res.status(502).json({ error: 'python_service_unavailable', detail: e.message })
  }
})

router.get('/sources/:id/preview', async (req, res) => {
  try {
    const data = await getKBSourcePreview(req.params.id)
    res.json(data)
  } catch (e: any) {
    res.status(502).json({ error: 'python_service_unavailable', detail: e.message })
  }
})

router.get('/sources/:id/chunks', async (req, res) => {
  try {
    const data = await getKBSourceChunks(req.params.id)
    res.json(data)
  } catch (e: any) {
    res.status(502).json({ error: 'python_service_unavailable', detail: e.message })
  }
})

router.put('/chunks/:id', async (req, res) => {
  try {
    const { text } = req.body
    const result = await updateChunk(req.params.id, text)
    res.json(result)
  } catch (e: any) {
    res.status(502).json({ error: 'python_service_unavailable', detail: e.message })
  }
})

router.get('/sources/:id/file', async (req, res) => {
  try {
    const pyUrl = process.env.PY_SERVICE_URL || 'http://127.0.0.1:8001'
    const targetUrl = `${pyUrl}/kb/sources/${req.params.id}/file`
    console.log(`[Proxy] Fetching file from: ${targetUrl}`)

    const response = await fetch(targetUrl)
    if (!response.ok) {
        console.error(`[Proxy] Upstream error: ${response.status} ${response.statusText}`)
        throw new Error(`Upstream error: ${response.status} ${response.statusText}`)
    }
    
    const contentType = response.headers.get('content-type')
    if (contentType) res.setHeader('Content-Type', contentType)

    const contentDisposition = response.headers.get('content-disposition')
    if (contentDisposition) res.setHeader('Content-Disposition', contentDisposition)
    
    if (!response.body) throw new Error('Empty response body from python service')
    
    response.body.pipe(res)
    response.body.on('error', (err: any) => {
       console.error('[Proxy] Stream error:', err)
       if (!res.headersSent) res.end()
    })
  } catch (e: any) {
    console.error('[Proxy] File fetch failed:', e)
    if (!res.headersSent) {
        res.status(502).json({ error: 'python_service_unavailable', detail: e.message })
    }
  }
})

router.post('/query', async (req, res) => {
  try {
    const { query } = req.body
    if (!query) return res.status(400).json({ error: 'Query is required' })
    const results = await searchKnowledgeBase(query)
    res.json(results)
  } catch (e: any) {
    res.status(502).json({ error: 'python_service_unavailable', detail: e.message })
  }
})

router.post('/process', async (req, res) => {
  // Stub for processing - effectively doing nothing but acknowledging
  res.json({ status: 'processed', files: [] })
})

export default router