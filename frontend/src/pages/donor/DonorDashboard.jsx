import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import Alert from '../../components/Alert'
import StatCard from '../../components/StatCard'
import StatusBadge from '../../components/StatusBadge'
import { getDonorDashboard } from '../../services/donors'
import { extractError } from '../../utils/errors'

function DonorDashboard() {
  const [data, setData] = useState(null)
  const [missingProfile, setMissingProfile] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true
    getDonorDashboard()
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
        <h1 className="text-2xl font-semibold text-gray-900">Donor dashboard</h1>
        <Alert type="info">
          Complete your donor profile to become visible to blood requests.{' '}
          <Link to="/donor/profile" className="underline">
            Create profile
          </Link>
        </Alert>
      </div>
    )
  }

  const { profile } = data
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-gray-900">Donor dashboard</h1>
      {!profile.is_eligible && (
        <Alert type="info">
          You are not eligible to donate right now: {profile.eligibility_reasons.join(' ')}
          {data.next_eligible_date && ` Next eligible date: ${data.next_eligible_date}.`}
        </Alert>
      )}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <StatCard label="Blood group" value={profile.blood_group_name} />
        <StatCard label="Availability" value={data.is_available ? 'Available' : 'Unavailable'} />
        <StatCard label="Completed donations" value={data.total_donations} hint={`${data.scheduled_donations} scheduled`} />
        <StatCard label="Unread notifications" value={data.unread_notifications} />
      </div>
      <section>
        <div className="mb-2 flex items-center justify-between">
          <h2 className="text-lg font-medium text-gray-900">Recent donations</h2>
          <Link to="/donor/donations" className="text-sm text-red-700 underline">
            View all
          </Link>
        </div>
        {data.recent_donations.length === 0 ? (
          <p className="text-sm text-gray-500">No donations recorded yet.</p>
        ) : (
          <ul className="divide-y divide-gray-200 rounded-lg border border-gray-200 bg-white">
            {data.recent_donations.map((d) => (
              <li key={d.id} className="flex items-center justify-between px-4 py-3 text-sm">
                <span>
                  {d.donation_date} at {d.bloodbank_name}
                </span>
                <StatusBadge value={d.status} />
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}

export default DonorDashboard
