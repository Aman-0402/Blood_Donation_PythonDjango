import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import Alert from '../../components/Alert'
import Button from '../../components/Button'
import StatusBadge from '../../components/StatusBadge'
import { useAuth } from '../../hooks/useAuth'
import { listRequests } from '../../services/requests'
import { extractError } from '../../utils/errors'
import { ROLES } from '../../utils/roles'

const STATUSES = ['pending', 'approved', 'matched', 'processing', 'completed', 'cancelled', 'rejected']

function RequestList() {
  const { user } = useAuth()
  const base = `/${user.role}/requests`
  const isAdmin = user.role === ROLES.ADMIN
  const [status, setStatus] = useState('')
  const [page, setPage] = useState(1)
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true
    listRequests({ page, ...(status && { status }) })
      .then((res) => active && setData(res))
      .catch((err) => active && setError(extractError(err)))
      .finally(() => active && setLoading(false))
    return () => {
      active = false
    }
  }, [page, status])

  const changeFilter = (value) => {
    setLoading(true)
    setPage(1)
    setStatus(value)
  }

  const goToPage = (next) => {
    setLoading(true)
    setPage(next)
  }

  if (error) return <Alert type="error">{error}</Alert>
  if (loading && !data) return <p className="text-gray-500">Loading...</p>

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h1 className="text-2xl font-semibold text-gray-900">{isAdmin ? 'Blood requests' : 'My blood requests'}</h1>
        {!isAdmin && (
          <Link to={`${base}/new`} className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700">
            New request
          </Link>
        )}
      </div>
      <div>
        <label htmlFor="status-filter" className="mr-2 text-sm text-gray-600">
          Status
        </label>
        <select
          id="status-filter"
          value={status}
          onChange={(e) => changeFilter(e.target.value)}
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
        <p className="text-sm text-gray-500">No requests found.</p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-gray-50 text-gray-600">
              <tr>
                <th className="px-4 py-2 font-medium">#</th>
                {isAdmin && <th className="px-4 py-2 font-medium">Requester</th>}
                <th className="px-4 py-2 font-medium">Blood</th>
                <th className="px-4 py-2 font-medium">Units</th>
                <th className="px-4 py-2 font-medium">Urgency</th>
                <th className="px-4 py-2 font-medium">Status</th>
                <th className="px-4 py-2 font-medium">Created</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data.results.map((r) => (
                <tr key={r.id}>
                  <td className="px-4 py-2">
                    <Link to={`${base}/${r.id}`} className="text-red-700 underline">
                      {r.id}
                    </Link>
                  </td>
                  {isAdmin && <td className="px-4 py-2">{r.requester_username}</td>}
                  <td className="px-4 py-2">{r.blood_group_name}</td>
                  <td className="px-4 py-2">{r.units_required}</td>
                  <td className="px-4 py-2">
                    <StatusBadge value={r.urgency} />
                  </td>
                  <td className="px-4 py-2">
                    <StatusBadge value={r.status} />
                  </td>
                  <td className="px-4 py-2">{new Date(r.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <div className="flex gap-2">
        <Button variant="secondary" disabled={!data.previous || loading} onClick={() => goToPage(page - 1)}>
          Previous
        </Button>
        <Button variant="secondary" disabled={!data.next || loading} onClick={() => goToPage(page + 1)}>
          Next
        </Button>
      </div>
    </div>
  )
}

export default RequestList
