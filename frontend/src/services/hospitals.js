import api from './api'

export async function getMyHospitalProfile() {
  try {
    const { data } = await api.get('/hospitals/me/')
    return data
  } catch (err) {
    if (err.response?.status === 404) return null
    throw err
  }
}

export async function createHospitalProfile(payload) {
  const { data } = await api.post('/hospitals/', payload)
  return data
}

export async function updateHospitalProfile(payload) {
  const { data } = await api.patch('/hospitals/me/', payload)
  return data
}

export async function getHospitalDashboard() {
  const { data } = await api.get('/hospitals/me/dashboard/')
  return data
}

export async function listHospitals(params = {}) {
  const { data } = await api.get('/hospitals/', { params })
  return data
}

export async function setHospitalVerified(id, verified) {
  const { data } = await api.post(`/hospitals/${id}/${verified ? 'verify' : 'unverify'}/`)
  return data
}
