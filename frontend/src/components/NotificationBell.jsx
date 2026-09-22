import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { getUnreadCount, listNotifications, markAllNotificationsRead, markNotificationRead } from '../services/notifications'
import { useAuth } from '../hooks/useAuth'

const TYPE_ICON = {
  request: '🩸',
  donation: '❤️',
  status_change: '🔔',
  verification: '✅',
  alert: '⚠️',
}

function timeAgo(iso) {
  const seconds = Math.floor((Date.now() - new Date(iso).getTime()) / 1000)
  if (seconds < 60) return 'just now'
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  return `${Math.floor(hours / 24)}d ago`
}

function NotificationBell() {
  const { user } = useAuth()
  const [open, setOpen] = useState(false)
  const [count, setCount] = useState(0)
  const [items, setItems] = useState([])
  const [loaded, setLoaded] = useState(false)
  const ref = useRef(null)

  useEffect(() => {
    let active = true
    const poll = () => getUnreadCount().then((c) => active && setCount(c)).catch(() => {})
    poll()
    const interval = setInterval(poll, 30000)
    return () => {
      active = false
      clearInterval(interval)
    }
  }, [user.id])

  useEffect(() => {
    function onClickOutside(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', onClickOutside)
    return () => document.removeEventListener('mousedown', onClickOutside)
  }, [])

  const openPanel = async () => {
    const next = !open
    setOpen(next)
    if (next && !loaded) {
      const res = await listNotifications({ page: 1 })
      setItems(res.results)
      setLoaded(true)
    }
  }

  const handleRead = async (id) => {
    await markNotificationRead(id)
    setItems(items.map((n) => (n.id === id ? { ...n, is_read: true } : n)))
    setCount((c) => Math.max(0, c - 1))
  }

  const handleReadAll = async () => {
    await markAllNotificationsRead()
    setItems(items.map((n) => ({ ...n, is_read: true })))
    setCount(0)
  }

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        aria-label="Notifications"
        onClick={openPanel}
        className="relative rounded-md p-2 text-gray-600 hover:bg-gray-100"
      >
        <span aria-hidden="true">🔔</span>
        {count > 0 && (
          <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-600 px-1 text-[10px] font-semibold text-white">
            {count > 99 ? '99+' : count}
          </span>
        )}
      </button>
      {open && (
        <div className="absolute right-0 z-20 mt-2 w-80 max-w-[90vw] rounded-lg border border-gray-200 bg-white shadow-lg">
          <div className="flex items-center justify-between border-b border-gray-100 px-3 py-2">
            <span className="text-sm font-medium text-gray-900">Notifications</span>
            {count > 0 && (
              <button type="button" onClick={handleReadAll} className="text-xs text-red-700 hover:underline">
                Mark all read
              </button>
            )}
          </div>
          <ul className="max-h-96 overflow-y-auto">
            {items.length === 0 && <li className="px-3 py-4 text-center text-sm text-gray-500">No notifications yet.</li>}
            {items.map((n) => (
              <li key={n.id} className={`border-b border-gray-50 px-3 py-2 text-sm ${n.is_read ? '' : 'bg-red-50/50'}`}>
                <div className="flex items-start gap-2">
                  <span aria-hidden="true">{TYPE_ICON[n.type] ?? '🔔'}</span>
                  <div className="min-w-0 flex-1">
                    <p className="text-gray-800">{n.message}</p>
                    <div className="mt-1 flex items-center justify-between">
                      <span className="text-xs text-gray-400">{timeAgo(n.created_at)}</span>
                      {!n.is_read && (
                        <button type="button" onClick={() => handleRead(n.id)} className="text-xs text-red-700 hover:underline">
                          Mark read
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              </li>
            ))}
          </ul>
          <Link
            to={`/${user.role}/notifications`}
            onClick={() => setOpen(false)}
            className="block border-t border-gray-100 px-3 py-2 text-center text-sm text-red-700 hover:bg-gray-50"
          >
            View all
          </Link>
        </div>
      )}
    </div>
  )
}

export default NotificationBell
