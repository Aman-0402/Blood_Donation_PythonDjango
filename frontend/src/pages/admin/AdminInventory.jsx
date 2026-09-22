import { useEffect, useState } from 'react'
import Alert from '../../components/Alert'
import Button from '../../components/Button'
import StatusBadge from '../../components/StatusBadge'
import { listAdminInventory, listAdminInventoryTransactions } from '../../services/admin'
import { extractError } from '../../utils/errors'

const STATUSES = ['available', 'reserved', 'expired', 'issued', 'discarded']

function Batches() {
  const [status, setStatus] = useState('available')
  const [page, setPage] = useState(1)
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true
    listAdminInventory({ page, ...(status && { status }) })
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
    <div className="space-y-3">
      <div>
        <label htmlFor="batch-status" className="mr-2 text-sm text-gray-600">
          Status
        </label>
        <select
          id="batch-status"
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
        <p className="text-sm text-gray-500">No batches found.</p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-gray-50 text-gray-600">
              <tr>
                <th className="px-4 py-2 font-medium">Blood bank</th>
                <th className="px-4 py-2 font-medium">Blood group</th>
                <th className="px-4 py-2 font-medium">Units</th>
                <th className="px-4 py-2 font-medium">Expires</th>
                <th className="px-4 py-2 font-medium">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data.results.map((b) => (
                <tr key={b.id}>
                  <td className="px-4 py-2">{b.bloodbank_name}</td>
                  <td className="px-4 py-2">{b.blood_group_name}</td>
                  <td className="px-4 py-2">{b.units}</td>
                  <td className="px-4 py-2">{b.expiry_date}</td>
                  <td className="px-4 py-2">
                    <StatusBadge value={b.status} />
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

function Transactions() {
  const [page, setPage] = useState(1)
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true
    listAdminInventoryTransactions({ page })
      .then((res) => active && setData(res))
      .catch((err) => active && setError(extractError(err)))
      .finally(() => active && setLoading(false))
    return () => {
      active = false
    }
  }, [page])

  if (error) return <Alert type="error">{error}</Alert>
  if (loading && !data) return <p className="text-gray-500">Loading...</p>

  return (
    <div className="space-y-3">
      {data.results.length === 0 ? (
        <p className="text-sm text-gray-500">No stock movements yet.</p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-gray-50 text-gray-600">
              <tr>
                <th className="px-4 py-2 font-medium">When</th>
                <th className="px-4 py-2 font-medium">Blood bank</th>
                <th className="px-4 py-2 font-medium">Type</th>
                <th className="px-4 py-2 font-medium">Blood group</th>
                <th className="px-4 py-2 font-medium">Units</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data.results.map((t) => (
                <tr key={t.id}>
                  <td className="px-4 py-2">{new Date(t.created_at).toLocaleString()}</td>
                  <td className="px-4 py-2">{t.bloodbank_name}</td>
                  <td className="px-4 py-2 capitalize">{t.type}</td>
                  <td className="px-4 py-2">{t.blood_group_name}</td>
                  <td className={`px-4 py-2 font-medium ${t.units < 0 ? 'text-red-700' : 'text-green-700'}`}>
                    {t.units > 0 ? `+${t.units}` : t.units}
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

function AdminInventory() {
  const [tab, setTab] = useState('batches')
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold text-gray-900">Inventory monitoring</h1>
      <div role="tablist" className="flex gap-2 border-b border-gray-200">
        {[
          { key: 'batches', label: 'Batches' },
          { key: 'transactions', label: 'Ledger' },
        ].map((t) => (
          <button
            key={t.key}
            type="button"
            role="tab"
            aria-selected={tab === t.key}
            onClick={() => setTab(t.key)}
            className={`-mb-px border-b-2 px-3 py-2 text-sm font-medium ${
              tab === t.key ? 'border-red-600 text-red-700' : 'border-transparent text-gray-600 hover:text-gray-900'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>
      {tab === 'batches' ? <Batches /> : <Transactions />}
    </div>
  )
}

export default AdminInventory
