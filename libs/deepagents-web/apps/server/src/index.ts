import express from 'express'
import cors from 'cors'
import chat from './routes/chat'
import config from './routes/config'
import prompts from './routes/prompts'
import agents from './routes/agents'
import tools from './routes/tools'
import kb from './routes/kb'
import skills from './routes/skills'
const app = express()
app.use(cors())
app.use(express.json())
app.get('/health', (req, res) => { res.json({ ok: true }) })
app.use('/api/v1/chat', chat)
app.use('/api/v1/config', config)
app.use('/api/v1/prompts', prompts)
app.use('/api/v1/agents', agents)
app.use('/api/v1/tools', tools)
app.use('/api/v1/kb', kb)
app.use('/api/v1/skills', skills)
const port = Number(process.env.PORT || 8005)
app.listen(port, () => {
  console.log(`server listening on http://localhost:${port}`)
})