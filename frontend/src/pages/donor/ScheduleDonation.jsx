import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Alert from '../../components/Alert'
import Button from '../../components/Button'
import FormField from '../../components/FormField'
import { listBankDirectory, scheduleDonation } from '../../services/donations'
import { extractError } from '../../utils/errors'

function toDateInput(date) {
  const pad = (n) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

function ScheduleDonation() {
  const navigate = useNavigate()
  const [banks, setBanks] = useState([])
  const [city, setCity] = useState('')
  const [form, setForm] = useState({ bloodbank: '', donation_date: '', collection_location: '' })
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true
    listBankDirectory(city.trim())
      .then((rows) => active && setBanks(rows))
      .catch((err) => active && setError(extractError(err)))
      .finally(() => active && setLoading(false))
    return () => {
      active = false
    }
  }, [city])

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSaving(true)
    try {
      await scheduleDonation({ ...form, bloodbank: Number(form.bloodbank) })
      navigate('/donor/donations', { replace: true })
    } catch (err) {
      setError(err.response?.status === 404 ? 'Create your donor profile first.' : extractError(err))
      setSaving(false)
    }
  }

  const today = toDateInput(new Date())

  return (
    <form onSubmit={handleSubmit} className="max-w-xl space-y-4">
      <h1 className="text-2xl font-semibold text-gray-900">Schedule a donation</h1>
      <Alert type="error">{error}</Alert>
      <FormField label="Filter blood banks by city" id="city" value={city} onChange={(e) => setCity(e.target.value)} />
      <FormField label="Blood bank" id="bloodbank" as="select" value={form.bloodbank} onChange={handleChange} required>
        <option value="">{loading ? 'Loading...' : 'Select...'}</option>
        {banks.map((b) => (
          <option key={b.id} value={b.id}>
            {b.name} ({b.city})
          </option>
        ))}
      </FormField>
      <FormField label="Date" id="donation_date" type="date" min={today} value={form.donation_date} onChange={handleChange} required />
      <FormField label="Location (optional, defaults to the bank's address)" id="collection_location" value={form.collection_location} onChange={handleChange} />
      <p className="text-xs text-gray-500">
        Your eligibility is checked for the date you choose. You can have one scheduled donation at a time.
      </p>
      <Button type="submit" disabled={saving}>
        {saving ? 'Scheduling...' : 'Schedule donation'}
      </Button>
    </form>
  )
}

export default ScheduleDonation
