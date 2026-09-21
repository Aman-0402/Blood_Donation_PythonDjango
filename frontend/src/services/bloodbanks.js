import api from './api'

export async function getMyBankProfile() {
  try {
    const { data } = await api.get('/bloodbanks/me/')
    return data
  } catch (err) {
    if (err.response?.status === 404) return null
    throw err
  }
}

export async function createBankProfile(payload) {
  const { data } = await api.post('/bloodbanks/', payload)
  return data
}

export async function updateBankProfile(payload) {
  const { data } = await api.patch('/bloodbanks/me/', payload)
  return data
}

export async function listBloodBanks(params = {}) {
  const { data } = await api.get('/bloodbanks/', { params })
  return data
}

export async function setBloodBankVerified(id, verified) {
  const { data } = await api.post(`/bloodbanks/${id}/${verified ? 'verify' : 'unverify'}/`)
  return data
}
