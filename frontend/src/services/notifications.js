import api from './api'

export async function listNotifications(params = {}) {
  const { data } = await api.get('/notifications/', { params })
  return data
}

export async function getUnreadCount() {
  const { data } = await api.get('/notifications/unread_count/')
  return data.count
}

export async function markNotificationRead(id) {
  const { data } = await api.post(`/notifications/${id}/read/`)
  return data
}

export async function markAllNotificationsRead() {
  const { data } = await api.post('/notifications/read-all/')
  return data
}
