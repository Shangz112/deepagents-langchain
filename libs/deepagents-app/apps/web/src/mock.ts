import axios from 'axios'
export function enableMock() {
  if (import.meta.env.VITE_USE_MOCK !== '1') return
  const r = axios.create()
  r.interceptors.request.use(cfg => cfg)
  r.interceptors.response.use(res => res)
}