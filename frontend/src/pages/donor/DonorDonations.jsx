import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import Alert from '../../components/Alert'
import Button from '../../components/Button'
import StatusBadge from '../../components/StatusBadge'
import { cancelDonation } from '../../services/donations'
import { getMyDonations } from '../../services/donors'
import { extractError } from '../../utils/errors'

function DonorDonations() {
  const [page, setPage] = useState(1)
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [actionError, setActionError] = useState('')
  const [loading, setLoading] = useState(true)
  const [busyId, setBusyId] = useState(null)
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    let active = true
    getMyDonations(page)
      .then((res) => active && setData(res))
      .catch((err) => active && setError(err.response?.status === 404 ? 'Create your donor profile first.' : extractError(err)))
      .finally(() => active && setLoading(false))
    return () => {
      active = false
    }
  }, [page, reloadKey])

  const goToPage = (next) => {
    setLoading(true)
    setPage(next)
  }

  const handleCancel = async (id) => {
    setActionError('')
    setBusyId(id)
    try {
      await cancelDonation(id)
      setReloadKey((k) => k + 1)
    } catch (err) {
      setActionError(extractError(err))
    } finally {
      setBusyId(null)
    }
  }

  if (error) return <Alert type="error">{error}</Alert>
  if (loading && !data) return <p className="text-gray-500">Loading...</p>

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h1 className="text-2xl font-semibold text-gray-900">Donation history</h1>
        <Link to="/donor/schedule" className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700">
          Schedule a donation
        </Link>
      </div>
      <Alert type="error">{actionError}</Alert>
      {data.results.length === 0 ? (
        <p className="text-sm text-gray-500">No donations yet.</p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-gray-50 text-gray-600">
              <tr>
                <th className="px-4 py-2 font-medium">Date</th>
                <th className="px-4 py-2 font-medium">Blood bank</th>
                <th className="px-4 py-2 font-medium">Units</th>
                <th className="px-4 py-2 font-medium">Status</th>
                <th className="px-4 py-2 font-medium" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data.results.map((d) => (
                <tr key={d.id}>
                  <td className="px-4 py-2">{d.donation_date}</td>
                  <td className="px-4 py-2">
                    {d.bloodbank_name}
                    {d.collection_location && <span className="block text-xs text-gray-500">{d.collection_location}</span>}
                  </td>
                  <td className="px-4 py-2">{d.quantity}</td>
                  <td className="px-4 py-2">
                    <StatusBadge value={d.status} />
                    {d.rejection_reason && <span className="block text-xs text-gray-500">{d.rejection_reason}</span>}
                  </td>
                  <td className="px-4 py-2 text-right">
                    {d.status === 'scheduled' && (
                      <Button variant="danger" disabled={busyId === d.id} onClick={() => handleCancel(d.id)}>
                        Cancel
                      </Button>
                    )}
                  </td>
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

export default DonorDonations
