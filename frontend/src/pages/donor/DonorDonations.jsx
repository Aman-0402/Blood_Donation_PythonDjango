import { useEffect, useState } from 'react'
import Alert from '../../components/Alert'
import Button from '../../components/Button'
import StatusBadge from '../../components/StatusBadge'
import { getMyDonations } from '../../services/donors'
import { extractError } from '../../utils/errors'

function DonorDonations() {
  const [page, setPage] = useState(1)
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true
    getMyDonations(page)
      .then((res) => active && setData(res))
      .catch((err) => active && setError(err.response?.status === 404 ? 'Create your donor profile first.' : extractError(err)))
      .finally(() => active && setLoading(false))
    return () => {
      active = false
    }
  }, [page])

  const goToPage = (next) => {
    setLoading(true)
    setPage(next)
  }

  if (error) return <Alert type="error">{error}</Alert>
  if (loading && !data) return <p className="text-gray-500">Loading...</p>

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold text-gray-900">Donation history</h1>
      {data.results.length === 0 ? (
        <p className="text-sm text-gray-500">No donations recorded yet.</p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-gray-50 text-gray-600">
              <tr>
                <th className="px-4 py-2 font-medium">Date</th>
                <th className="px-4 py-2 font-medium">Blood bank</th>
                <th className="px-4 py-2 font-medium">Units</th>
                <th className="px-4 py-2 font-medium">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data.results.map((d) => (
                <tr key={d.id}>
                  <td className="px-4 py-2">{d.donation_date}</td>
                  <td className="px-4 py-2">{d.bloodbank_name}</td>
                  <td className="px-4 py-2">{d.quantity}</td>
                  <td className="px-4 py-2">
                    <StatusBadge value={d.status} />
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
