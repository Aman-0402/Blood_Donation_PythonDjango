import api from './api'

export async function getAdminDashboard() {
  const { data } = await api.get('/admin/dashboard/')
  return data
}

export async function listUsers(params = {}) {
  const { data } = await api.get('/users/', { params })
  return data
}

export async function deactivateUser(id) {
  const { data } = await api.post(`/users/${id}/deactivate/`)
  return data
}

export async function activateUser(id) {
  const { data } = await api.post(`/users/${id}/activate/`)
  return data
}

export async function listAdminInventory(params = {}) {
  const { data } = await api.get('/inventory/', { params })
  return data
}

export async function listAdminInventoryTransactions(params = {}) {
  const { data } = await api.get('/inventory/transactions/', { params })
  return data
}

export async function listAdminDonations(params = {}) {
  const { data } = await api.get('/donations/', { params })
  return data
}
