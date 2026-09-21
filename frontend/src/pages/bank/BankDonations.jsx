import { useEffect, useState } from 'react'
import Alert from '../../components/Alert'
import Button from '../../components/Button'
import StatusBadge from '../../components/StatusBadge'
import { completeDonation, listDonations, rejectDonation } from '../../services/donations'
import { extractError } from '../../utils/errors'

const STATUSES = ['scheduled', 'completed', 'cancelled', 'rejected']

function BankDonations() {
  const [status, setStatus] = useState('scheduled')
  const [page, setPage] = useState(1)
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(true)
  const [reloadKey, setReloadKey] = useState(0)
  const [busyId, setBusyId] = useState(null)
  const [quantities, setQuantities] = useState({})
  const [rejecting, setRejecting] = useState(null)
  const [reason, setReason] = useState('')

  useEffect(() => {
    let active = true
    listDonations({ page, ...(status && { status }) })
      .then((res) => active && setData(res))
      .catch((err) => active && setError(extractError(err)))
      .finally(() => active && setLoading(false))
    return () => {
      active = false
    }
  }, [page, status, reloadKey])

  const reload = () => setReloadKey((k) => k + 1)

  const run = async (id, action, success) => {
    setError('')
    setMessage('')
    setBusyId(id)
    try {
      await action()
      setMessage(success)
      setRejecting(null)
      setReason('')
      reload()
    } catch (err) {
      setError(extractError(err))
    } finally {
      setBusyId(null)
    }
  }

  const today = new Date().toISOString().slice(0, 10)

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold text-gray-900">Donations</h1>
      <Alert type="error">{error}</Alert>
      <Alert type="success">{message}</Alert>
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
      {loading && !data ? (
        <p className="text-gray-500">Loading...</p>
      ) : data && data.results.length === 0 ? (
        <p className="text-sm text-gray-500">No donations found.</p>
      ) : (
        data && (
          <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white">
            <table className="min-w-full text-left text-sm">
              <thead className="bg-gray-50 text-gray-600">
                <tr>
                  <th className="px-4 py-2 font-medium">Date</th>
                  <th className="px-4 py-2 font-medium">Donor</th>
                  <th className="px-4 py-2 font-medium">Blood</th>
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
                      {d.donor_name}
                      {d.donor_phone && <span className="block text-xs text-gray-500">{d.donor_phone}</span>}
                    </td>
                    <td className="px-4 py-2">{d.blood_group_name}</td>
                    <td className="px-4 py-2">
                      {d.status === 'scheduled' ? (
                        <input
                          aria-label={`Units for donation ${d.id}`}
                          type="number"
                          min={1}
                          max={10}
                          value={quantities[d.id] ?? 1}
                          onChange={(e) => setQuantities({ ...quantities, [d.id]: e.target.value })}
                          className="w-16 rounded-md border border-gray-300 px-2 py-1"
                        />
                      ) : (
                        d.quantity
                      )}
                    </td>
                    <td className="px-4 py-2">
                      <StatusBadge value={d.status} />
                      {d.rejection_reason && <span className="block text-xs text-gray-500">{d.rejection_reason}</span>}
                    </td>
                    <td className="space-x-2 px-4 py-2 text-right">
                      {d.status === 'scheduled' && (
                        <>
                          <Button
                            disabled={busyId === d.id || d.donation_date > today}
                            title={d.donation_date > today ? 'Available on the donation date' : ''}
                            onClick={() =>
                              run(d.id, () => completeDonation(d.id, Number(quantities[d.id] ?? 1)), 'Donation completed and added to stock.')
                            }
                          >
                            Complete
                          </Button>
                          <Button variant="danger" disabled={busyId === d.id} onClick={() => setRejecting(rejecting === d.id ? null : d.id)}>
                            Reject
                          </Button>
                        </>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      )}
      {rejecting && (
        <form
          onSubmit={(e) => {
            e.preventDefault()
            run(rejecting, () => rejectDonation(rejecting, reason), 'Donation rejected.')
          }}
          className="flex flex-wrap items-end gap-3 rounded-lg border border-gray-200 bg-white p-4"
        >
          <div className="min-w-64 flex-1">
            <label htmlFor="reject-reason" className="block text-sm font-medium text-gray-700">
              Reason for rejecting donation #{rejecting}
            </label>
            <input
              id="reject-reason"
              value={reason}
              maxLength={255}
              onChange={(e) => setReason(e.target.value)}
              required
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            />
          </div>
          <Button type="submit" variant="danger">
            Confirm rejection
          </Button>
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
    </div>
  )
}

export default BankDonations
