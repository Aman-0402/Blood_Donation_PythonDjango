import { useEffect, useState } from 'react'
import Alert from '../../components/Alert'
import Button from '../../components/Button'
import StatusBadge from '../../components/StatusBadge'
import { extractError } from '../../utils/errors'

const DEFAULT_COLUMNS = [
  { label: 'Name', render: (org) => org.name },
  { label: 'City', render: (org) => org.city },
  { label: 'License', render: (org) => org.license_number },
]

function AdminVerification({ title, fetchList, setVerified, columns = DEFAULT_COLUMNS }) {
  const [filter, setFilter] = useState('false')
  const [page, setPage] = useState(1)
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [busyId, setBusyId] = useState(null)
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    let active = true
    fetchList({ page, ...(filter && { verified: filter }) })
      .then((res) => active && setData(res))
      .catch((err) => active && setError(extractError(err)))
      .finally(() => active && setLoading(false))
    return () => {
      active = false
    }
  }, [fetchList, page, filter, reloadKey])

  const changeFilter = (value) => {
    setLoading(true)
    setPage(1)
    setFilter(value)
  }

  const toggle = async (org) => {
    setError('')
    setBusyId(org.id)
    try {
      await setVerified(org.id, !org.is_verified)
      setReloadKey((k) => k + 1)
    } catch (err) {
      setError(extractError(err))
    } finally {
      setBusyId(null)
    }
  }

  if (loading && !data) return <p className="text-gray-500">Loading...</p>

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold text-gray-900">{title}</h1>
      <Alert type="error">{error}</Alert>
      <div>
        <label htmlFor="verified-filter" className="mr-2 text-sm text-gray-600">
          Show
        </label>
        <select
          id="verified-filter"
          value={filter}
          onChange={(e) => changeFilter(e.target.value)}
          className="rounded-md border border-gray-300 px-2 py-1 text-sm"
        >
          <option value="false">Awaiting verification</option>
          <option value="true">Verified</option>
          <option value="">All</option>
        </select>
      </div>
      {data && data.results.length === 0 ? (
        <p className="text-sm text-gray-500">Nothing found.</p>
      ) : (
        data && (
          <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white">
            <table className="min-w-full text-left text-sm">
              <thead className="bg-gray-50 text-gray-600">
                <tr>
                  {columns.map((c) => (
                    <th key={c.label} className="px-4 py-2 font-medium">
                      {c.label}
                    </th>
                  ))}
                  <th className="px-4 py-2 font-medium">Status</th>
                  <th className="px-4 py-2 font-medium" />
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {data.results.map((org) => (
                  <tr key={org.id}>
                    {columns.map((c) => (
                      <td key={c.label} className="px-4 py-2">
                        {c.render(org)}
                      </td>
                    ))}
                    <td className="px-4 py-2">
                      <StatusBadge value={org.is_verified ? 'verified' : 'unverified'} />
                    </td>
                    <td className="px-4 py-2 text-right">
                      <Button
                        variant={org.is_verified ? 'danger' : 'primary'}
                        disabled={busyId === org.id}
                        onClick={() => toggle(org)}
                      >
                        {org.is_verified ? 'Unverify' : 'Verify'}
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      )}
      {data && (
        <div className="flex gap-2">
          <Button variant="secondary" disabled={!data.previous || loading} onClick={() => { setLoading(true); setPage(page - 1) }}>
            Previous
          </Button>
          <Button variant="secondary" disabled={!data.next || loading} onClick={() => { setLoading(true); setPage(page + 1) }}>
            Next
          </Button>
        </div>
      )}
    </div>
  )
}

export default AdminVerification
