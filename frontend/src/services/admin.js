import api from './api'

export async function getAdminDashboard() {
  const { data } = await api.get('/admin/dashboard/')
  return data
}
