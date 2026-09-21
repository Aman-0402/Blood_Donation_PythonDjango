import { useEffect, useState } from 'react'
import Alert from '../../components/Alert'
import Button from '../../components/Button'
import FormField from '../../components/FormField'
import { useBloodGroups } from '../../hooks/useBloodGroups'
import { createDonorProfile, getMyDonorProfile, updateDonorProfile } from '../../services/donors'
import { extractError } from '../../utils/errors'

const emptyForm = {
  blood_group: '',
  date_of_birth: '',
  city: '',
  address: '',
  last_donation_date: '',
  is_available: true,
  eligibility_notes: '',
}

function toForm(profile) {
  return {
    blood_group: String(profile.blood_group),
    date_of_birth: profile.date_of_birth,
    city: profile.city,
    address: profile.address,
    last_donation_date: profile.last_donation_date ?? '',
    is_available: profile.is_available,
    eligibility_notes: profile.eligibility_notes,
  }
}

function DonorProfile() {
  const bloodGroups = useBloodGroups()
  const [profile, setProfile] = useState(null)
  const [form, setForm] = useState(emptyForm)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [saved, setSaved] = useState('')

  useEffect(() => {
    let active = true
    getMyDonorProfile()
      .then((p) => {
        if (!active || !p) return
        setProfile(p)
        setForm(toForm(p))
      })
      .catch((err) => active && setError(extractError(err)))
      .finally(() => active && setLoading(false))
    return () => {
      active = false
    }
  }, [])

  const handleChange = (e) => {
    const { name, type, value, checked } = e.target
    setForm({ ...form, [name]: type === 'checkbox' ? checked : value })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSaved('')
    setSaving(true)
    const payload = {
      ...form,
      blood_group: Number(form.blood_group),
      last_donation_date: form.last_donation_date || null,
    }
    try {
      const result = profile ? await updateDonorProfile(payload) : await createDonorProfile(payload)
      setProfile(result)
      setForm(toForm(result))
      setSaved('Profile saved.')
    } catch (err) {
      setError(extractError(err))
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <p className="text-gray-500">Loading...</p>

  return (
    <form onSubmit={handleSubmit} className="max-w-xl space-y-4">
      <h1 className="text-2xl font-semibold text-gray-900">
        {profile ? 'Donor profile' : 'Create donor profile'}
      </h1>
      <Alert type="error">{error}</Alert>
      <Alert type="success">{saved}</Alert>
      {profile && (
        <Alert type={profile.is_eligible ? 'success' : 'info'}>
          {profile.is_eligible
            ? 'You are currently eligible to donate.'
            : `Not eligible right now: ${profile.eligibility_reasons.join(' ')}${
                profile.next_eligible_date ? ` Next eligible date: ${profile.next_eligible_date}.` : ''
              }`}
        </Alert>
      )}
      <FormField label="Blood group" id="blood_group" as="select" value={form.blood_group} onChange={handleChange} required>
        <option value="">Select...</option>
        {bloodGroups.map((g) => (
          <option key={g.id} value={g.id}>
            {g.name}
          </option>
        ))}
      </FormField>
      <FormField label="Date of birth" id="date_of_birth" type="date" value={form.date_of_birth} onChange={handleChange} required />
      <FormField label="City" id="city" value={form.city} onChange={handleChange} required />
      <FormField label="Address" id="address" value={form.address} onChange={handleChange} />
      <FormField label="Last donation date (if any)" id="last_donation_date" type="date" value={form.last_donation_date} onChange={handleChange} />
      <FormField label="Eligibility notes (medical conditions, medication)" id="eligibility_notes" as="textarea" rows={3} value={form.eligibility_notes} onChange={handleChange} />
      <label className="flex items-center gap-2 text-sm text-gray-700">
        <input type="checkbox" name="is_available" checked={form.is_available} onChange={handleChange} />
        I am available to donate
      </label>
      <Button type="submit" disabled={saving}>
        {saving ? 'Saving...' : 'Save profile'}
      </Button>
    </form>
  )
}

export default DonorProfile
