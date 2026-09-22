import api from './api'

export async function getMyDonorProfile() {
  try {
    const { data } = await api.get('/donors/me/')
    return data
  } catch (err) {
    if (err.response?.status === 404) return null
    throw err
  }
}

export async function createDonorProfile(payload) {
  const { data } = await api.post('/donors/', payload)
  return data
}

export async function updateDonorProfile(payload) {
  const { data } = await api.patch('/donors/me/', payload)
  return data
}

export async function getDonorDashboard() {
  const { data } = await api.get('/donors/me/dashboard/')
  return data
}

export async function getMyDonations(page = 1) {
  const { data } = await api.get('/donors/me/donations/', { params: { page } })
  return data
}

export async function listDonors(params = {}) {
  const { data } = await api.get('/donors/', { params })
  return data
}

export async function setDonorVerified(id, verified) {
  const { data } = await api.post(`/donors/${id}/${verified ? 'verify' : 'unverify'}/`)
  return data
}
