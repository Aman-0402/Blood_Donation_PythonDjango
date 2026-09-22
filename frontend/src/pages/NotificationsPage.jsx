import { useEffect, useState } from 'react'
import Alert from '../components/Alert'
import Button from '../components/Button'
import { listNotifications, markAllNotificationsRead, markNotificationRead } from '../services/notifications'
import { extractError } from '../utils/errors'

const TYPE_ICON = {
  request: '🩸',
  donation: '❤️',
  status_change: '🔔',
  verification: '✅',
  alert: '⚠️',
}

function NotificationsPage() {
  const [filter, setFilter] = useState('')
  const [page, setPage] = useState(1)
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    let active = true
    listNotifications({ page, ...(filter && { is_read: filter }) })
      .then((res) => active && setData(res))
      .catch((err) => active && setError(extractError(err)))
      .finally(() => active && setLoading(false))
    return () => {
      active = false
    }
  }, [page, filter, reloadKey])

  const changeFilter = (value) => {
    setLoading(true)
    setPage(1)
    setFilter(value)
  }

  const handleRead = async (id) => {
    await markNotificationRead(id)
    setReloadKey((k) => k + 1)
  }

  const handleReadAll = async () => {
    await markAllNotificationsRead()
    setReloadKey((k) => k + 1)
  }

  if (error) return <Alert type="error">{error}</Alert>
  if (loading && !data) return <p className="text-gray-500">Loading...</p>

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h1 className="text-2xl font-semibold text-gray-900">Notifications</h1>
        <Button variant="secondary" onClick={handleReadAll}>
          Mark all read
        </Button>
      </div>
      <div>
        <label htmlFor="notif-filter" className="mr-2 text-sm text-gray-600">
          Show
        </label>
        <select
          id="notif-filter"
          value={filter}
          onChange={(e) => changeFilter(e.target.value)}
          className="rounded-md border border-gray-300 px-2 py-1 text-sm"
        >
          <option value="">All</option>
          <option value="false">Unread</option>
          <option value="true">Read</option>
        </select>
      </div>
      {data.results.length === 0 ? (
        <p className="text-sm text-gray-500">No notifications.</p>
      ) : (
        <ul className="divide-y divide-gray-200 rounded-lg border border-gray-200 bg-white">
          {data.results.map((n) => (
            <li key={n.id} className={`flex items-start gap-3 px-4 py-3 text-sm ${n.is_read ? '' : 'bg-red-50/40'}`}>
              <span aria-hidden="true">{TYPE_ICON[n.type] ?? '🔔'}</span>
              <div className="min-w-0 flex-1">
                <p className="text-gray-800">{n.message}</p>
                <p className="mt-1 text-xs text-gray-400">{new Date(n.created_at).toLocaleString()}</p>
              </div>
              {!n.is_read && (
                <Button variant="secondary" onClick={() => handleRead(n.id)}>
                  Mark read
                </Button>
              )}
            </li>
          ))}
        </ul>
      )}
      <div className="flex gap-2">
        <Button variant="secondary" disabled={!data.previous || loading} onClick={() => { setLoading(true); setPage(page - 1) }}>
          Previous
        </Button>
        <Button variant="secondary" disabled={!data.next || loading} onClick={() => { setLoading(true); setPage(page + 1) }}>
          Next
        </Button>
      </div>
    </div>
  )
}

export default NotificationsPage
