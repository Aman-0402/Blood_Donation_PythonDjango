import api from './api'

export async function searchBlood(params = {}) {
  const { data } = await api.get('/search/blood/', { params })
  return data
}

export async function searchDonors(params = {}) {
  const { data } = await api.get('/search/donors/', { params })
  return data
}

export async function searchHospitals(params = {}) {
  const { data } = await api.get('/search/hospitals/', { params })
  return data
}

export async function getRequestMatches(id) {
  const { data } = await api.get(`/requests/${id}/matches/`)
  return data
}

export async function getRequestResponses(id) {
  const { data } = await api.get(`/requests/${id}/responses/`)
  return data
}

export async function listOpenRequests(page = 1) {
  const { data } = await api.get('/donors/me/requests/', { params: { page } })
  return data
}

export async function respondToRequest(id, answer) {
  const { data } = await api.post(`/donors/me/requests/${id}/respond/`, { answer })
  return data
}
