import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import Alert from '../../components/Alert'
import StatCard from '../../components/StatCard'
import { getAdminDashboard } from '../../services/admin'
import { extractError } from '../../utils/errors'

function AdminDashboard() {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true
    getAdminDashboard()
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
      <h1 className="text-2xl font-semibold text-gray-900">Admin dashboard</h1>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        <StatCard label="Total users" value={data.total_users} />
        <StatCard label="Donors" value={data.total_donors} />
        <StatCard
          label="Hospitals"
          value={data.total_hospitals}
          hint={`${data.verified_hospitals} verified`}
        />
        <StatCard
          label="Blood banks"
          value={data.total_bloodbanks}
          hint={`${data.verified_bloodbanks} verified`}
        />
        <StatCard label="Pending requests" value={data.pending_requests} />
        <StatCard label="Completed requests" value={data.completed_requests} />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <section>
          <h2 className="mb-2 text-lg font-medium text-gray-900">Blood requests by status</h2>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
            {Object.entries(data.request_counts).map(([status, count]) => (
              <div key={status} className="rounded-md border border-gray-200 bg-white p-3 text-center">
                <p className="text-xs capitalize text-gray-500">{status}</p>
                <p className="text-xl text-gray-900">{count}</p>
              </div>
            ))}
          </div>
          <Link to="/admin/requests" className="mt-2 inline-block text-sm text-red-700 underline">
            View all requests
          </Link>
        </section>

        <section>
          <h2 className="mb-2 text-lg font-medium text-gray-900">Donations by status</h2>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            {Object.entries(data.donation_counts).map(([status, count]) => (
              <div key={status} className="rounded-md border border-gray-200 bg-white p-3 text-center">
                <p className="text-xs capitalize text-gray-500">{status}</p>
                <p className="text-xl text-gray-900">{count}</p>
              </div>
            ))}
          </div>
        </section>
      </div>

      <section>
        <h2 className="mb-2 text-lg font-medium text-gray-900">Blood inventory (usable, all banks)</h2>
        <div className="grid grid-cols-4 gap-2 md:grid-cols-8">
          {data.blood_inventory.map((b) => (
            <div key={b.blood_group} className="rounded-md border border-gray-200 bg-white p-2 text-center">
              <p className="text-sm font-semibold text-red-700">{b.blood_group_name}</p>
              <p className="text-lg text-gray-900">{b.units_available}</p>
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2 className="mb-2 text-lg font-medium text-gray-900">Users by role</h2>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-5">
          {Object.entries(data.users_by_role).map(([role, count]) => (
            <div key={role} className="rounded-md border border-gray-200 bg-white p-3 text-center">
              <p className="text-xs capitalize text-gray-500">{role}</p>
              <p className="text-xl text-gray-900">{count}</p>
            </div>
          ))}
        </div>
      </section>

      <div className="flex flex-wrap gap-3">
        <Link to="/admin/hospitals" className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50">
          Manage hospitals
        </Link>
        <Link to="/admin/bloodbanks" className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50">
          Manage blood banks
        </Link>
      </div>
    </div>
  )
}

export default AdminDashboard
