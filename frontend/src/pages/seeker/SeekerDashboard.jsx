import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import Alert from '../../components/Alert'
import StatCard from '../../components/StatCard'
import StatusBadge from '../../components/StatusBadge'
import { getSeekerDashboard } from '../../services/requests'
import { extractError } from '../../utils/errors'

function SeekerDashboard() {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true
    getSeekerDashboard()
      .then((res) => active && setData(res))
      .catch((err) => active && setError(extractError(err)))
      .finally(() => active && setLoading(false))
    return () => {
      active = false
    }
  }, [])

  if (loading) return <p className="text-gray-500">Loading...</p>
  if (error) return <Alert type="error">{error}</Alert>

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h1 className="text-2xl font-semibold text-gray-900">My dashboard</h1>
        <Link to="/seeker/requests/new" className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700">
          New request
        </Link>
      </div>
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <StatCard label="Active requests" value={data.active_requests} />
        <StatCard label="Pending" value={data.request_counts.pending} />
        <StatCard label="Completed" value={data.request_counts.completed} />
        <StatCard label="Unread notifications" value={data.unread_notifications} />
      </div>
      <section>
        <div className="mb-2 flex items-center justify-between">
          <h2 className="text-lg font-medium text-gray-900">Recent requests</h2>
          <Link to="/seeker/requests" className="text-sm text-red-700 underline">
            View all
          </Link>
        </div>
        {data.recent_requests.length === 0 ? (
          <p className="text-sm text-gray-500">No requests yet.</p>
        ) : (
          <ul className="divide-y divide-gray-200 rounded-lg border border-gray-200 bg-white">
            {data.recent_requests.map((r) => (
              <li key={r.id} className="flex items-center justify-between px-4 py-3 text-sm">
                <Link to={`/seeker/requests/${r.id}`} className="text-red-700 underline">
                  #{r.id} {r.blood_group_name} x{r.units_required}
                </Link>
                <StatusBadge value={r.status} />
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}

export default SeekerDashboard
