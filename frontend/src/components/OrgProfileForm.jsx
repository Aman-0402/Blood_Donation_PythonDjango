import { useEffect, useState } from 'react'
import Alert from './Alert'
import Button from './Button'
import FormField from './FormField'
import StatusBadge from './StatusBadge'
import { extractError } from '../utils/errors'

const emptyForm = { name: '', city: '', address: '', license_number: '' }

const toForm = (p) => ({ name: p.name, city: p.city, address: p.address, license_number: p.license_number })

function OrgProfileForm({ noun, service }) {
  const [profile, setProfile] = useState(null)
  const [form, setForm] = useState(emptyForm)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [saved, setSaved] = useState('')

  useEffect(() => {
    let active = true
    service
      .get()
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
  }, [service])

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSaved('')
    setSaving(true)
    try {
      const result = profile ? await service.update(form) : await service.create(form)
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
      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-semibold text-gray-900">
          {profile ? `${noun} profile` : `Create ${noun.toLowerCase()} profile`}
        </h1>
        {profile && <StatusBadge value={profile.is_verified ? 'verified' : 'unverified'} />}
      </div>
      <Alert type="error">{error}</Alert>
      <Alert type="success">{saved}</Alert>
      {profile && !profile.is_verified && (
        <Alert type="info">An administrator will review your license number and verify your {noun.toLowerCase()}.</Alert>
      )}
      <FormField label={`${noun} name`} id="name" value={form.name} onChange={handleChange} required />
      <FormField label="License number" id="license_number" value={form.license_number} onChange={handleChange} required />
      <FormField label="City" id="city" value={form.city} onChange={handleChange} required />
      <FormField label="Address" id="address" value={form.address} onChange={handleChange} />
      <Button type="submit" disabled={saving}>
        {saving ? 'Saving...' : 'Save profile'}
      </Button>
    </form>
  )
}

export default OrgProfileForm
