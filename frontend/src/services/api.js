import axios from 'axios'
import { tokens } from './tokens'

const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api'

const api = axios.create({ baseURL })

api.interceptors.request.use((config) => {
  if (tokens.access) {
    config.headers.Authorization = `Bearer ${tokens.access}`
  }
  return config
})

let refreshPromise = null

const isAuthUrl = (url = '') =>
  url.includes('/auth/login') || url.includes('/auth/refresh') || url.includes('/auth/register')

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config
    const canRefresh =
      error.response?.status === 401 &&
      original &&
      !original._retry &&
      tokens.refresh &&
      !isAuthUrl(original.url)

    if (!canRefresh) return Promise.reject(error)

    original._retry = true
    try {
      refreshPromise ??= axios
        .post(`${baseURL}/auth/refresh/`, { refresh: tokens.refresh })
        .finally(() => {
          refreshPromise = null
        })
      const { data } = await refreshPromise
      tokens.set(data.access, data.refresh)
      original.headers.Authorization = `Bearer ${data.access}`
      return api(original)
    } catch {
      tokens.clear()
      window.dispatchEvent(new Event('auth:logout'))
      return Promise.reject(error)
    }
  },
)

export default api
