import { useEffect, useState } from 'react'
import Alert from '../../components/Alert'
import Button from '../../components/Button'
import StatusBadge from '../../components/StatusBadge'
import { listHospitals, setHospitalVerified } from '../../services/hospitals'
import { extractError } from '../../utils/errors'

function AdminHospitals() {
  const [filter, setFilter] = useState('false')
  const [page, setPage] = useState(1)
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [busyId, setBusyId] = useState(null)
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    let active = true
    listHospitals({ page, ...(filter && { verified: filter }) })
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

  const toggle = async (hospital) => {
    setError('')
    setBusyId(hospital.id)
    try {
      await setHospitalVerified(hospital.id, !hospital.is_verified)
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
      <h1 className="text-2xl font-semibold text-gray-900">Hospitals</h1>
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
        <p className="text-sm text-gray-500">No hospitals found.</p>
      ) : (
        data && (
          <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white">
            <table className="min-w-full text-left text-sm">
              <thead className="bg-gray-50 text-gray-600">
                <tr>
                  <th className="px-4 py-2 font-medium">Name</th>
                  <th className="px-4 py-2 font-medium">City</th>
                  <th className="px-4 py-2 font-medium">License</th>
                  <th className="px-4 py-2 font-medium">Status</th>
                  <th className="px-4 py-2 font-medium" />
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {data.results.map((h) => (
                  <tr key={h.id}>
                    <td className="px-4 py-2">{h.name}</td>
                    <td className="px-4 py-2">{h.city}</td>
                    <td className="px-4 py-2">{h.license_number}</td>
                    <td className="px-4 py-2">
                      <StatusBadge value={h.is_verified ? 'verified' : 'unverified'} />
                    </td>
                    <td className="px-4 py-2 text-right">
                      <Button
                        variant={h.is_verified ? 'danger' : 'primary'}
                        disabled={busyId === h.id}
                        onClick={() => toggle(h)}
                      >
                        {h.is_verified ? 'Unverify' : 'Verify'}
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

export default AdminHospitals
