import request from 'supertest'
import express from 'express'
import cors from 'cors'
import config from '../src/routes/config'
const app = express()
app.use(cors())
app.use(express.json())
app.use('/api/v1/config', config)
test('config get', async () => { const res = await request(app).get('/api/v1/config'); expect(res.status).toBe(200) })