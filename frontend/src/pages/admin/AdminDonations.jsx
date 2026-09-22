import { useEffect, useState } from 'react'
import Alert from '../../components/Alert'
import Button from '../../components/Button'
import StatusBadge from '../../components/StatusBadge'
import { listAdminDonations } from '../../services/admin'
import { extractError } from '../../utils/errors'

const STATUSES = ['scheduled', 'completed', 'cancelled', 'rejected']

function AdminDonations() {
  const [status, setStatus] = useState('')
  const [page, setPage] = useState(1)
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true
    listAdminDonations({ page, ...(status && { status }) })
      .then((res) => active && setData(res))
      .catch((err) => active && setError(extractError(err)))
      .finally(() => active && setLoading(false))
    return () => {
      active = false
    }
  }, [page, status])

  if (error) return <Alert type="error">{error}</Alert>
  if (loading && !data) return <p className="text-gray-500">Loading...</p>

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold text-gray-900">Donation monitoring</h1>
      <div>
        <label htmlFor="donation-status" className="mr-2 text-sm text-gray-600">
          Status
        </label>
        <select
          id="donation-status"
          value={status}
          onChange={(e) => {
            setLoading(true)
            setPage(1)
            setStatus(e.target.value)
          }}
          className="rounded-md border border-gray-300 px-2 py-1 text-sm"
        >
          <option value="">All</option>
          {STATUSES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </div>
      {data.results.length === 0 ? (
        <p className="text-sm text-gray-500">No donations found.</p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-gray-50 text-gray-600">
              <tr>
                <th className="px-4 py-2 font-medium">Date</th>
                <th className="px-4 py-2 font-medium">Blood bank</th>
                <th className="px-4 py-2 font-medium">Blood group</th>
                <th className="px-4 py-2 font-medium">Units</th>
                <th className="px-4 py-2 font-medium">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data.results.map((d) => (
                <tr key={d.id}>
                  <td className="px-4 py-2">{d.donation_date}</td>
                  <td className="px-4 py-2">{d.bloodbank_name}</td>
                  <td className="px-4 py-2">{d.blood_group_name}</td>
                  <td className="px-4 py-2">{d.quantity}</td>
                  <td className="px-4 py-2">
                    <StatusBadge value={d.status} />
                    {d.rejection_reason && <span className="block text-xs text-gray-500">{d.rejection_reason}</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
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

export default AdminDonations
