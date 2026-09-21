import api from './api'

export async function listRequests(params = {}) {
  const { data } = await api.get('/requests/', { params })
  return data
}

export async function getRequest(id) {
  const { data } = await api.get(`/requests/${id}/`)
  return data
}

export async function createRequest(payload) {
  const { data } = await api.post('/requests/', payload)
  return data
}

export async function updateRequest(id, payload) {
  const { data } = await api.patch(`/requests/${id}/`, payload)
  return data
}

export async function cancelRequest(id) {
  const { data } = await api.post(`/requests/${id}/cancel/`)
  return data
}

export async function setRequestStatus(id, status, note = '') {
  const { data } = await api.post(`/requests/${id}/status/`, { status, note })
  return data
}

export async function bankAction(id, action) {
  const { data } = await api.post(`/requests/${id}/${action}/`)
  return data
}

export async function getRequestHistory(id) {
  const { data } = await api.get(`/requests/${id}/history/`)
  return data
}
