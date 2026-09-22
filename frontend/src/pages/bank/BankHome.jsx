import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import Alert from '../../components/Alert'
import StatCard from '../../components/StatCard'
import { useAuth } from '../../hooks/useAuth'
import { getBankDashboard } from '../../services/bloodbanks'
import { extractError } from '../../utils/errors'

function BankHome() {
  const { user } = useAuth()
  const [data, setData] = useState(null)
  const [missingProfile, setMissingProfile] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true
    getBankDashboard()
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
        <h1 className="text-2xl font-semibold text-gray-900">Blood bank</h1>
        <Alert type="info">
          Create your blood bank profile so an administrator can verify it.{' '}
          <Link to="/bloodbank/profile" className="underline">
            Create profile
          </Link>
        </Alert>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-gray-900">{data.profile.name}</h1>
      {!user.is_verified && (
        <Alert type="info">
          Your blood bank is awaiting verification. You can view stock, but adding, issuing and fulfilling requests are disabled until an administrator verifies you.
        </Alert>
      )}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <StatCard label="Units collected (all time)" value={data.units_collected} />
        <StatCard label="Units issued" value={data.units_issued} />
        <StatCard label="Units expired" value={data.units_expired} />
        <StatCard label="Scheduled donations" value={data.scheduled_donations} />
      </div>

      <section>
        <h2 className="mb-2 text-lg font-medium text-gray-900">Current stock (usable units)</h2>
        <div className="grid grid-cols-2 gap-2 md:grid-cols-4">
          {data.stock_by_blood_group.map((row) => (
            <div key={row.blood_group} className="rounded-md border border-gray-200 bg-white p-3">
              <p className="text-sm font-semibold text-red-700">{row.blood_group_name}</p>
              <p className="text-2xl text-gray-900">{row.units_available}</p>
              {data.expiring_within_7_days[row.blood_group] > 0 && (
                <p className="text-xs text-orange-700">{data.expiring_within_7_days[row.blood_group]} expiring within 7 days</p>
              )}
            </div>
          ))}
        </div>
        <div className="mt-2 flex gap-3">
          <Link to="/bloodbank/inventory" className="text-sm text-red-700 underline">
            Manage inventory
          </Link>
          {data.open_requests_for_fulfilment > 0 && (
            <Link to="/bloodbank/requests" className="text-sm text-red-700 underline">
              {data.open_requests_for_fulfilment} request(s) open for fulfilment
            </Link>
          )}
        </div>
      </section>
    </div>
  )
}

export default BankHome
