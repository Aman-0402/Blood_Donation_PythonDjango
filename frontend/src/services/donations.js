import api from './api'

export async function scheduleDonation(payload) {
  const { data } = await api.post('/donations/', payload)
  return data
}

export async function cancelDonation(id) {
  const { data } = await api.post(`/donations/${id}/cancel/`)
  return data
}

export async function listDonations(params = {}) {
  const { data } = await api.get('/donations/', { params })
  return data
}

export async function completeDonation(id, quantity) {
  const { data } = await api.post(`/donations/${id}/complete/`, { quantity })
  return data
}

export async function rejectDonation(id, reason) {
  const { data } = await api.post(`/donations/${id}/reject/`, { reason })
  return data
}

export async function listBankDirectory(city) {
  const { data } = await api.get('/bloodbanks/directory/', { params: city ? { city } : {} })
  return data
}
