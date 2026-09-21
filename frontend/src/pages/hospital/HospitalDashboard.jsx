import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import Alert from '../../components/Alert'
import StatCard from '../../components/StatCard'
import StatusBadge from '../../components/StatusBadge'
import { getHospitalDashboard } from '../../services/hospitals'
import { extractError } from '../../utils/errors'

function HospitalDashboard() {
  const [data, setData] = useState(null)
  const [missingProfile, setMissingProfile] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true
    getHospitalDashboard()
      .then((res) => active && setData(res))
      .catch((err) => {
        if (!active) return
        if (err.response?.status === 404) setMissingProfile(true)
        else setError(extractError(err))
      })
      .finally(() => active && setLoading(false))
    return () => {
      active = false
    }
  }, [])

  if (loading) return <p className="text-gray-500">Loading...</p>
  if (error) return <Alert type="error">{error}</Alert>
  if (missingProfile) {
    return (
      <div className="space-y-3">
        <h1 className="text-2xl font-semibold text-gray-900">Hospital dashboard</h1>
        <Alert type="info">
          Set up your hospital profile to get verified and start requesting blood.{' '}
          <Link to="/hospital/profile" className="underline">
            Create profile
          </Link>
        </Alert>
      </div>
    )
  }

  const counts = data.request_counts
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h1 className="text-2xl font-semibold text-gray-900">{data.profile.name}</h1>
        <StatusBadge value={data.is_verified ? 'verified' : 'unverified'} />
      </div>
      {!data.is_verified && (
        <Alert type="info">
          Your hospital is awaiting verification by an administrator. You cannot request blood or search availability until it is verified.
        </Alert>
      )}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <StatCard label="Active requests" value={data.active_requests} />
        <StatCard label="Pending" value={counts.pending} />
        <StatCard label="Completed" value={counts.completed} />
        <StatCard label="Unread notifications" value={data.unread_notifications} />
      </div>

      <section>
        <h2 className="mb-2 text-lg font-medium text-gray-900">Blood available across blood banks</h2>
        <div className="grid grid-cols-4 gap-2 md:grid-cols-8">
          {data.available_blood.map((b) => (
            <div key={b.blood_group} className="rounded-md border border-gray-200 bg-white p-2 text-center">
              <p className="text-sm font-semibold text-red-700">{b.blood_group_name}</p>
              <p className="text-lg text-gray-900">{b.units_available}</p>
            </div>
          ))}
        </div>
        <Link to="/hospital/availability" className="mt-2 inline-block text-sm text-red-700 underline">
          Search by city
        </Link>
      </section>

      <section>
        <div className="mb-2 flex items-center justify-between">
          <h2 className="text-lg font-medium text-gray-900">Recent requests</h2>
          <Link to="/hospital/requests" className="text-sm text-red-700 underline">
            View all
          </Link>
        </div>
        {data.recent_requests.length === 0 ? (
          <p className="text-sm text-gray-500">No requests yet.</p>
        ) : (
          <ul className="divide-y divide-gray-200 rounded-lg border border-gray-200 bg-white">
            {data.recent_requests.map((r) => (
              <li key={r.id} className="flex items-center justify-between px-4 py-3 text-sm">
                <Link to={`/hospital/requests/${r.id}`} className="text-red-700 underline">
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

export default HospitalDashboard
