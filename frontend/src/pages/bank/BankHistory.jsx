import { useEffect, useState } from 'react'
import Alert from '../../components/Alert'
import Button from '../../components/Button'
import { listTransactions } from '../../services/inventory'
import { extractError } from '../../utils/errors'

const TYPES = ['collection', 'issue', 'expired', 'adjustment']

function BankHistory() {
  const [type, setType] = useState('')
  const [page, setPage] = useState(1)
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true
    listTransactions({ page, ...(type && { type }) })
      .then((res) => active && setData(res))
      .catch((err) => active && setError(extractError(err)))
      .finally(() => active && setLoading(false))
    return () => {
      active = false
    }
  }, [page, type])

  if (error) return <Alert type="error">{error}</Alert>
  if (loading && !data) return <p className="text-gray-500">Loading...</p>

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold text-gray-900">Inventory history</h1>
      <div>
        <label htmlFor="tx-type" className="mr-2 text-sm text-gray-600">
          Type
        </label>
        <select
          id="tx-type"
          value={type}
          onChange={(e) => {
            setLoading(true)
            setPage(1)
            setType(e.target.value)
          }}
          className="rounded-md border border-gray-300 px-2 py-1 text-sm"
        >
          <option value="">All</option>
          {TYPES.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
      </div>
      {data.results.length === 0 ? (
        <p className="text-sm text-gray-500">No stock movements yet.</p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-gray-50 text-gray-600">
              <tr>
                <th className="px-4 py-2 font-medium">When</th>
                <th className="px-4 py-2 font-medium">Type</th>
                <th className="px-4 py-2 font-medium">Blood group</th>
                <th className="px-4 py-2 font-medium">Units</th>
                <th className="px-4 py-2 font-medium">Request</th>
                <th className="px-4 py-2 font-medium">Note</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data.results.map((t) => (
                <tr key={t.id}>
                  <td className="px-4 py-2">{new Date(t.created_at).toLocaleString()}</td>
                  <td className="px-4 py-2 capitalize">{t.type}</td>
                  <td className="px-4 py-2">{t.blood_group_name}</td>
                  <td className={`px-4 py-2 font-medium ${t.units < 0 ? 'text-red-700' : 'text-green-700'}`}>
                    {t.units > 0 ? `+${t.units}` : t.units}
                  </td>
                  <td className="px-4 py-2">{t.request ? `#${t.request}` : '-'}</td>
                  <td className="px-4 py-2">{t.note || '-'}</td>
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

export default BankHistory
