import fetch from 'node-fetch'
import FormData from 'form-data'

const PY_URL = process.env.PY_SERVICE_URL || 'http://127.0.0.1:8001'
export async function createSession() {
  const r = await fetch(`${PY_URL}/sessions`, { method: 'POST' })
  return r.json()
}
export async function getSession(id: string) {
  const r = await fetch(`${PY_URL}/sessions/${id}`)
  return r.json()
}
export async function deleteSession(id: string) {
  const r = await fetch(`${PY_URL}/sessions/${id}`, { method: 'DELETE' })
  return r.json()
}
export async function sendMessage(id: string, content: string, tools?: any) {
  const r = await fetch(`${PY_URL}/sessions/${id}/messages`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ content, tools }) })
  return r.json()
}
export function streamSession(id: string) {
  const url = `${PY_URL}/sessions/${id}/stream`
  return url
}
export async function getPrompts(): Promise<any[]> {
  const r = await fetch(`${PY_URL}/prompts`)
  return r.json() as Promise<any[]>
}
export async function getSessionConfig(id: string) {
  const r = await fetch(`${PY_URL}/sessions/${id}/config`)
  return r.json()
}
export async function getSessionContext(id: string) {
  const r = await fetch(`${PY_URL}/sessions/${id}/context`)
  return r.json()
}
export async function updateSessionConfig(id: string, config: any) {
  const r = await fetch(`${PY_URL}/sessions/${id}/config`, { 
    method: 'POST', 
    headers: { 'content-type': 'application/json' }, 
    body: JSON.stringify(config) 
  })
  return r.json()
}
export async function listSkills() {
  const r = await fetch(`${PY_URL}/skills`)
  const j = await r.json()
  return j
}
export async function updateConfig(config: any) {
  const r = await fetch(`${PY_URL}/config`, { 
    method: 'POST', 
    headers: { 'content-type': 'application/json' }, 
    body: JSON.stringify({
      api_key: config.apiKey,
      base_url: config.baseUrl,
      model: config.modelName
    }) 
  })
  return r.json()
}
export async function getConfig() {
  const r = await fetch(`${PY_URL}/config`)
  return r.json()
}

// Prompts Persistence
export async function savePrompts(prompts: any[]) {
  const r = await fetch(`${PY_URL}/prompts`, { 
    method: 'POST', 
    headers: { 'content-type': 'application/json' }, 
    body: JSON.stringify(prompts) 
  })
  return r.json()
}

export async function getQuickStarters() {
  const r = await fetch(`${PY_URL}/prompts/quick-starters`)
  return r.json()
}

export async function saveQuickStarters(starters: any[]) {
  const r = await fetch(`${PY_URL}/prompts/quick-starters`, { 
    method: 'POST', 
    headers: { 'content-type': 'application/json' }, 
    body: JSON.stringify(starters) 
  })
  return r.json()
}

// KB Persistence
export async function getKBSources() {
  const r = await fetch(`${PY_URL}/kb/sources`)
  return r.json()
}
export async function saveKBSource(source: any) {
  const r = await fetch(`${PY_URL}/kb/sources`, { 
    method: 'POST', 
    headers: { 'content-type': 'application/json' }, 
    body: JSON.stringify(source) 
  })
  return r.json()
}

export async function uploadKBSource(file: Express.Multer.File, template: string = "default") {
  const form = new FormData()
  form.append('file', file.buffer, file.originalname)
  form.append('template', template)
  
  const r = await fetch(`${PY_URL}/kb/upload`, { 
    method: 'POST', 
    body: form,
    headers: form.getHeaders()
  })
  
  if (!r.ok) {
      const txt = await r.text()
      throw new Error(`Upload failed: ${r.status} ${txt}`)
  }
  return r.json()
}
export async function deleteKBSource(id: string) {
  const r = await fetch(`${PY_URL}/kb/sources/${id}`, { method: 'DELETE' })
  return r.json()
}
export async function renameKBSource(id: string, name: string) {
  const r = await fetch(`${PY_URL}/kb/sources/${id}`, {
    method: 'PUT',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ name })
  })
  return r.json()
}
export async function getKBSourcePreview(id: string) {
  const r = await fetch(`${PY_URL}/kb/sources/${id}/preview`)
  if (!r.ok) {
     const txt = await r.text()
     throw new Error(`Preview failed: ${r.status} ${txt}`)
  }
  return r.json()
}

export async function getKBSourceChunks(id: string) {
  const r = await fetch(`${PY_URL}/kb/sources/${id}/chunks`)
  return r.json()
}

export async function updateChunk(id: string, text: string) {
  const r = await fetch(`${PY_URL}/kb/chunks/${id}`, {
    method: 'PUT',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ text })
  })
  return r.json()
}
export async function searchKnowledgeBase(query: string) {
  const r = await fetch(`${PY_URL}/kb/query`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ query })
  })
  return r.json()
}

// Agents Persistence
export async function getSubAgents() {
  const r = await fetch(`${PY_URL}/agents/subagents`)
  return r.json()
}
export async function saveSubAgent(agent: any) {
  const r = await fetch(`${PY_URL}/agents/subagents`, { 
    method: 'POST', 
    headers: { 'content-type': 'application/json' }, 
    body: JSON.stringify(agent) 
  })
  return r.json()
}
export async function clearSubAgents() {
  const r = await fetch(`${PY_URL}/agents/subagents`, { method: 'DELETE' })
  return r.json()
}

export async function saveFeedback(data: any) {
  const r = await fetch(`${PY_URL}/feedback`, { 
    method: 'POST', 
    headers: { 'content-type': 'application/json' }, 
    body: JSON.stringify(data) 
  })
  return r.json()
}

export async function exportFeedback() {
  const r = await fetch(`${PY_URL}/feedback/export`)
  return r.json()
}
