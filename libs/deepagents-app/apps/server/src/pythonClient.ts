import fetch from 'node-fetch'
const PY_URL = process.env.PY_SERVICE_URL || 'http://127.0.0.1:8002'
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