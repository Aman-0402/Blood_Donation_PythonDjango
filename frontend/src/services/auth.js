import api from './api'
import { tokens } from './tokens'

export async function login(username, password) {
  const { data } = await api.post('/auth/login/', { username, password })
  tokens.set(data.access, data.refresh)
  return data.user
}

export async function register(payload) {
  const { data } = await api.post('/auth/register/', payload)
  tokens.set(data.access, data.refresh)
  return data.user
}

export async function logout() {
  const refresh = tokens.refresh
  try {
    if (refresh) await api.post('/auth/logout/', { refresh })
  } finally {
    tokens.clear()
  }
}

export async function fetchMe() {
  const { data } = await api.get('/auth/me/')
  return data
}

export async function changePassword(oldPassword, newPassword) {
  await api.post('/auth/change-password/', {
    old_password: oldPassword,
    new_password: newPassword,
  })
}
