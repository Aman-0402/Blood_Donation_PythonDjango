import { useEffect, useState } from 'react'
import Alert from '../../components/Alert'
import Button from '../../components/Button'
import FormField from '../../components/FormField'
import StatusBadge from '../../components/StatusBadge'
import { useBloodGroups } from '../../hooks/useBloodGroups'
import { addUnits, adjustBatch, expireStock, listBatches } from '../../services/inventory'
import { extractError } from '../../utils/errors'

const STATUSES = ['available', 'reserved', 'expired', 'issued', 'discarded']
const emptyForm = { blood_group: '', units: 1, collection_date: '', expiry_date: '', note: '' }

function BankInventory() {
  const bloodGroups = useBloodGroups()
  const [status, setStatus] = useState('available')
  const [page, setPage] = useState(1)
  const [data, setData] = useState(null)
  const [reloadKey, setReloadKey] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [form, setForm] = useState(emptyForm)
  const [adding, setAdding] = useState(false)
  const [adjusting, setAdjusting] = useState(null)
  const [adjustForm, setAdjustForm] = useState({ delta: '', reason: '' })

  useEffect(() => {
    let active = true
    listBatches({ page, ...(status && { status }) })
      .then((res) => active && setData(res))
      .catch((err) => active && setError(extractError(err)))
      .finally(() => active && setLoading(false))
    return () => {
      active = false
    }
  }, [page, status, reloadKey])

  const reload = () => setReloadKey((k) => k + 1)

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const handleAdd = async (e) => {
    e.preventDefault()
    setError('')
    setMessage('')
    setAdding(true)
    const payload = { blood_group: Number(form.blood_group), units: Number(form.units), note: form.note }
    if (form.collection_date) payload.collection_date = form.collection_date
    if (form.expiry_date) payload.expiry_date = form.expiry_date
    try {
      await addUnits(payload)
      setForm(emptyForm)
      setMessage('Blood units added.')
      reload()
    } catch (err) {
      setError(extractError(err))
    } finally {
      setAdding(false)
    }
  }

  const handleExpire = async () => {
    setError('')
    setMessage('')
    try {
      const { expired_units: units } = await expireStock()
      setMessage(units ? `${units} expired unit(s) removed from stock.` : 'No expired units found.')
      reload()
    } catch (err) {
      setError(extractError(err))
    }
  }

  const handleAdjust = async (e) => {
    e.preventDefault()
    setError('')
    setMessage('')
    try {
      await adjustBatch(adjusting, Number(adjustForm.delta), adjustForm.reason)
      setAdjusting(null)
      setAdjustForm({ delta: '', reason: '' })
      setMessage('Batch adjusted.')
      reload()
    } catch (err) {
      setError(extractError(err))
    }
  }

  const changeStatus = (value) => {
    setLoading(true)
    setPage(1)
    setStatus(value)
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-gray-900">Inventory</h1>
      <Alert type="error">{error}</Alert>
      <Alert type="success">{message}</Alert>

      <form onSubmit={handleAdd} className="space-y-3 rounded-lg border border-gray-200 bg-white p-4">
        <h2 className="text-lg font-medium text-gray-900">Add collected blood</h2>
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          <FormField label="Blood group" id="blood_group" as="select" value={form.blood_group} onChange={handleChange} required>
            <option value="">Select...</option>
            {bloodGroups.map((g) => (
              <option key={g.id} value={g.id}>
                {g.name}
              </option>
            ))}
          </FormField>
          <FormField label="Units" id="units" type="number" min={1} max={1000} value={form.units} onChange={handleChange} required />
          <FormField label="Collected on" id="collection_date" type="date" value={form.collection_date} onChange={handleChange} />
          <FormField label="Expires on" id="expiry_date" type="date" value={form.expiry_date} onChange={handleChange} />
        </div>
        <p className="text-xs text-gray-500">Leave dates empty to use today and the default 35-day shelf life.</p>
        <Button type="submit" disabled={adding}>
          {adding ? 'Adding...' : 'Add units'}
        </Button>
      </form>

      <section className="space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <label htmlFor="batch-status" className="mr-2 text-sm text-gray-600">
              Status
            </label>
            <select
              id="batch-status"
              value={status}
              onChange={(e) => changeStatus(e.target.value)}
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
          <Button variant="secondary" onClick={handleExpire}>
            Remove expired units
          </Button>
        </div>
        {loading && !data ? (
          <p className="text-gray-500">Loading...</p>
        ) : data && data.results.length === 0 ? (
          <p className="text-sm text-gray-500">No batches found.</p>
        ) : (
          data && (
            <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white">
              <table className="min-w-full text-left text-sm">
                <thead className="bg-gray-50 text-gray-600">
                  <tr>
                    <th className="px-4 py-2 font-medium">Blood group</th>
                    <th className="px-4 py-2 font-medium">Units left</th>
                    <th className="px-4 py-2 font-medium">Collected</th>
                    <th className="px-4 py-2 font-medium">Expires</th>
                    <th className="px-4 py-2 font-medium">Status</th>
                    <th className="px-4 py-2 font-medium" />
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {data.results.map((b) => (
                    <tr key={b.id}>
                      <td className="px-4 py-2">{b.blood_group_name}</td>
                      <td className="px-4 py-2">{b.units}</td>
                      <td className="px-4 py-2">{b.collection_date}</td>
                      <td className="px-4 py-2">{b.expiry_date}</td>
                      <td className="px-4 py-2">
                        <StatusBadge value={b.status} />
                      </td>
                      <td className="px-4 py-2 text-right">
                        {b.status === 'available' && (
                          <Button variant="secondary" onClick={() => setAdjusting(adjusting === b.id ? null : b.id)}>
                            Adjust
                          </Button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )
        )}
        {adjusting && (
          <form onSubmit={handleAdjust} className="flex flex-wrap items-end gap-3 rounded-lg border border-gray-200 bg-white p-4">
            <div className="w-32">
              <FormField label="Change (+/-)" id="delta" type="number" value={adjustForm.delta} onChange={(e) => setAdjustForm({ ...adjustForm, delta: e.target.value })} required />
            </div>
            <div className="min-w-48 flex-1">
              <FormField label="Reason" id="reason" value={adjustForm.reason} onChange={(e) => setAdjustForm({ ...adjustForm, reason: e.target.value })} required />
            </div>
            <Button type="submit">Apply to batch #{adjusting}</Button>
          </form>
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
      </section>
    </div>
  )
}

export default BankInventory
