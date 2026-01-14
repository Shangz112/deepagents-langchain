import request from 'supertest'
import express from 'express'
import cors from 'cors'
import chat from '../src/routes/chat'
const app = express()
app.use(cors())
app.use(express.json())
app.use('/api/v1/chat', chat)
test('health session create', async () => {
  const res = await request(app).post('/api/v1/chat/sessions')
  expect(res.status).toBe(200)
})