import { useEffect, useState } from 'react'
import Alert from '../../components/Alert'
import Button from '../../components/Button'
import StatusBadge from '../../components/StatusBadge'
import { listOpenRequests, respondToRequest } from '../../services/search'
import { extractError } from '../../utils/errors'

function DonorRequests() {
  const [page, setPage] = useState(1)
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [actionError, setActionError] = useState('')
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(true)
  const [busyId, setBusyId] = useState(null)
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    let active = true
    listOpenRequests(page)
      .then((res) => active && setData(res))
      .catch((err) => active && setError(err.response?.status === 404 ? 'Create your donor profile first.' : extractError(err)))
      .finally(() => active && setLoading(false))
    return () => {
      active = false
    }
  }, [page, reloadKey])

  const respond = async (id, answer) => {
    setActionError('')
    setMessage('')
    setBusyId(id)
    try {
      await respondToRequest(id, answer)
      setMessage(answer === 'accepted' ? 'Thank you. The requester can now see your name and phone number.' : 'Response saved.')
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
      <h1 className="text-2xl font-semibold text-gray-900">Requests near you</h1>
      <p className="text-sm text-gray-600">
        Open requests in your city that your blood group can safely serve. Patient details stay private. If you accept, your name and phone number are shared with that requester so you can coordinate.
      </p>
      <Alert type="error">{actionError}</Alert>
      <Alert type="success">{message}</Alert>
      {data.results.length === 0 ? (
        <p className="text-sm text-gray-500">No matching requests right now.</p>
      ) : (
        <ul className="space-y-3">
          {data.results.map((r) => (
            <li key={r.id} className="rounded-lg border border-gray-200 bg-white p-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="font-medium text-gray-900">
                  {r.blood_group_name} needed, {r.units_required} unit(s)
                </p>
                <StatusBadge value={r.urgency} />
              </div>
              <p className="mt-1 text-sm text-gray-600">
                {r.location} ({r.city}){r.hospital_name ? `, ${r.hospital_name}` : ''}
              </p>
              <div className="mt-3 flex items-center gap-2">
                <Button disabled={busyId === r.id || r.my_response === 'accepted'} onClick={() => respond(r.id, 'accepted')}>
                  {r.my_response === 'accepted' ? 'Accepted' : 'I can donate'}
                </Button>
                <Button variant="secondary" disabled={busyId === r.id || r.my_response === 'declined'} onClick={() => respond(r.id, 'declined')}>
                  {r.my_response === 'declined' ? 'Declined' : 'Decline'}
                </Button>
              </div>
            </li>
          ))}
        </ul>
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

export default DonorRequests
