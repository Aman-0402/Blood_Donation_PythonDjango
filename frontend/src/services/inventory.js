import api from './api'

export async function getInventorySummary() {
  const { data } = await api.get('/inventory/summary/')
  return data
}

export async function listBatches(params = {}) {
  const { data } = await api.get('/inventory/', { params })
  return data
}

export async function addUnits(payload) {
  const { data } = await api.post('/inventory/', payload)
  return data
}

export async function issueUnits(payload) {
  const { data } = await api.post('/inventory/issue/', payload)
  return data
}

export async function expireStock() {
  const { data } = await api.post('/inventory/expire/')
  return data
}

export async function adjustBatch(id, delta, reason) {
  const { data } = await api.post(`/inventory/${id}/adjust/`, { delta, reason })
  return data
}

export async function listTransactions(params = {}) {
  const { data } = await api.get('/inventory/transactions/', { params })
  return data
}
