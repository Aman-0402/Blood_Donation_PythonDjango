import api from './api'

export async function getDonationReport() {
  const { data } = await api.get('/reports/donations/')
  return data
}

export async function getRequestReport() {
  const { data } = await api.get('/reports/requests/')
  return data
}

export async function getInventoryReport() {
  const { data } = await api.get('/reports/inventory/')
  return data
}
