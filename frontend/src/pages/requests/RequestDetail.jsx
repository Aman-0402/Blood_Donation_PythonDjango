import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import Alert from '../../components/Alert'
import Button from '../../components/Button'
import StatusBadge from '../../components/StatusBadge'
import { useAuth } from '../../hooks/useAuth'
import { bankAction, cancelRequest, getRequest, getRequestHistory, setRequestStatus } from '../../services/requests'
import { extractError } from '../../utils/errors'
import { ROLES } from '../../utils/roles'

const OWNER_CANCELLABLE = ['pending', 'approved', 'matched']

const fetchRequestAndHistory = (id, includeHistory) =>
  Promise.all([getRequest(id), includeHistory ? getRequestHistory(id) : Promise.resolve([])])

function Detail({ label, children }) {
  return (
    <div>
      <dt className="text-xs uppercase text-gray-500">{label}</dt>
      <dd className="text-sm text-gray-900">{children || '-'}</dd>
    </div>
  )
}

function RequestDetail() {
  const { id } = useParams()
  const { user } = useAuth()
  const base = `/${user.role}/requests`
  const isAdmin = user.role === ROLES.ADMIN
  const isBank = user.role === ROLES.BLOODBANK
  const [request, setRequest] = useState(null)
  const [history, setHistory] = useState([])
  const [note, setNote] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    let active = true
    fetchRequestAndHistory(id, !isBank)
      .then(([r, h]) => {
        if (!active) return
        setRequest(r)
        setHistory(h)
      })
      .catch((err) => active && setError(err.response?.status === 404 ? 'Request not found.' : extractError(err)))
      .finally(() => active && setLoading(false))
    return () => {
      active = false
    }
  }, [id, isBank])

  const run = async (action) => {
    setError('')
    setBusy(true)
    try {
      await action()
      setNote('')
      const [r, h] = await fetchRequestAndHistory(id, !isBank)
      setRequest(r)
      setHistory(h)
    } catch (err) {
      setError(extractError(err))
    } finally {
      setBusy(false)
    }
  }

  if (loading) return <p className="text-gray-500">Loading...</p>
  if (!request) return <Alert type="error">{error}</Alert>

  const isRequester = !isAdmin && !isBank
  const canEdit = isRequester && request.status === 'pending'
  const canCancel = isRequester && OWNER_CANCELLABLE.includes(request.status)
  const assignedToMe = isBank && request.fulfilled_by_bloodbank != null
  const bankActions = []
  if (isBank && request.status === 'approved' && !assignedToMe) bankActions.push(['accept', 'Accept request', 'primary'])
  if (assignedToMe && request.status === 'matched') {
    bankActions.push(['dispatch', 'Dispatch blood', 'primary'], ['release', 'Release request', 'danger'])
  }
  if (assignedToMe && request.status === 'processing') bankActions.push(['complete', 'Mark delivered', 'primary'])

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h1 className="text-2xl font-semibold text-gray-900">Request #{request.id}</h1>
        <div className="flex gap-2">
          <StatusBadge value={request.urgency} />
          <StatusBadge value={request.status} />
        </div>
      </div>
      <Alert type="error">{error}</Alert>

      <dl className="grid grid-cols-2 gap-4 rounded-lg border border-gray-200 bg-white p-4 md:grid-cols-3">
        <Detail label="Blood group">{request.blood_group_name}</Detail>
        <Detail label="Units required">{request.units_required}</Detail>
        <Detail label="Location">{request.location}</Detail>
        <Detail label="Patient">{request.patient_name}</Detail>
        <Detail label="Contact phone">{request.contact_phone}</Detail>
        <Detail label="Hospital">{request.hospital_name}</Detail>
        {isAdmin && <Detail label="Requester">{request.requester_username}</Detail>}
        <Detail label="Fulfilled by">{request.fulfilled_by_bloodbank_name}</Detail>
        <Detail label="Created">{new Date(request.created_at).toLocaleString()}</Detail>
        <div className="col-span-2 md:col-span-3">
          <Detail label="Notes">{request.notes}</Detail>
        </div>
      </dl>

      <div className="flex flex-wrap gap-2">
        {canEdit && (
          <Link to={`${base}/${request.id}/edit`} className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50">
            Edit
          </Link>
        )}
        {canCancel && (
          <Button variant="danger" disabled={busy} onClick={() => run(() => cancelRequest(request.id))}>
            Cancel request
          </Button>
        )}
        {bankActions.map(([action, label, variant]) => (
          <Button key={action} variant={variant} disabled={busy} onClick={() => run(() => bankAction(request.id, action))}>
            {label}
          </Button>
        ))}
        <Link to={base} className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50">
          Back to list
        </Link>
      </div>
      {isBank && !assignedToMe && (
        <Alert type="info">
          Patient details are shown after your blood bank accepts this request. Accepting requires enough usable stock of this blood group.
        </Alert>
      )}

      {isAdmin && request.allowed_next_statuses.length > 0 && (
        <section className="space-y-2 rounded-lg border border-gray-200 bg-white p-4">
          <h2 className="text-lg font-medium text-gray-900">Update status</h2>
          <label htmlFor="note" className="block text-sm text-gray-600">
            Note (optional)
          </label>
          <input
            id="note"
            value={note}
            maxLength={500}
            onChange={(e) => setNote(e.target.value)}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
          />
          <div className="flex flex-wrap gap-2">
            {request.allowed_next_statuses.map((next) => (
              <Button
                key={next}
                variant={next === 'rejected' || next === 'cancelled' ? 'danger' : 'primary'}
                disabled={busy}
                onClick={() => run(() => setRequestStatus(request.id, next, note))}
              >
                Mark {next}
              </Button>
            ))}
          </div>
        </section>
      )}

      {!isBank && (
      <section>
        <h2 className="mb-2 text-lg font-medium text-gray-900">History</h2>
        <ol className="space-y-2 border-l-2 border-gray-200 pl-4">
          {history.map((h) => (
            <li key={h.id} className="text-sm">
              <span className="font-medium capitalize">{h.to_status}</span>
              <span className="text-gray-500">
                {' '}
                by {h.changed_by_username ?? 'system'} on {new Date(h.created_at).toLocaleString()}
              </span>
              {h.note && <p className="text-gray-600">{h.note}</p>}
            </li>
          ))}
        </ol>
      </section>
      )}
    </div>
  )
}

export default RequestDetail
