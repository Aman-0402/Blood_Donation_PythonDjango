import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import Alert from '../../components/Alert'
import Button from '../../components/Button'
import FormField from '../../components/FormField'
import { useAuth } from '../../hooks/useAuth'
import { useBloodGroups } from '../../hooks/useBloodGroups'
import { createRequest, getRequest, updateRequest } from '../../services/requests'
import { extractError } from '../../utils/errors'
import { ROLES } from '../../utils/roles'

const emptyForm = {
  patient_name: '',
  contact_phone: '',
  blood_group: '',
  units_required: 1,
  urgency: 'normal',
  location: '',
  notes: '',
}

function RequestForm() {
  const { id } = useParams()
  const { user } = useAuth()
  const navigate = useNavigate()
  const bloodGroups = useBloodGroups()
  const base = `/${user.role}/requests`
  const isEdit = Boolean(id)
  const needsPatient = user.role !== ROLES.HOSPITAL
  const [form, setForm] = useState(emptyForm)
  const [loading, setLoading] = useState(isEdit)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!isEdit) return undefined
    let active = true
    getRequest(id)
      .then((r) => {
        if (!active) return
        setForm({
          patient_name: r.patient_name,
          contact_phone: r.contact_phone,
          blood_group: String(r.blood_group),
          units_required: r.units_required,
          urgency: r.urgency,
          location: r.location,
          notes: r.notes,
        })
      })
      .catch((err) => active && setError(extractError(err)))
      .finally(() => active && setLoading(false))
    return () => {
      active = false
    }
  }, [id, isEdit])

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSaving(true)
    const payload = { ...form, blood_group: Number(form.blood_group), units_required: Number(form.units_required) }
    try {
      const saved = isEdit ? await updateRequest(id, payload) : await createRequest(payload)
      navigate(`${base}/${saved.id}`, { replace: true })
    } catch (err) {
      setError(extractError(err))
      setSaving(false)
    }
  }

  if (loading) return <p className="text-gray-500">Loading...</p>

  return (
    <form onSubmit={handleSubmit} className="max-w-xl space-y-4">
      <h1 className="text-2xl font-semibold text-gray-900">{isEdit ? `Edit request #${id}` : 'New blood request'}</h1>
      <Alert type="error">{error}</Alert>
      {user.role === ROLES.HOSPITAL && !user.is_verified && (
        <Alert type="info">Your hospital must be verified by an administrator before it can request blood.</Alert>
      )}
      <FormField label={needsPatient ? 'Patient name' : 'Patient name (optional)'} id="patient_name" value={form.patient_name} onChange={handleChange} required={needsPatient} />
      <FormField label="Contact phone" id="contact_phone" type="tel" value={form.contact_phone} onChange={handleChange} />
      <div className="grid grid-cols-2 gap-3">
        <FormField label="Blood group" id="blood_group" as="select" value={form.blood_group} onChange={handleChange} required>
          <option value="">Select...</option>
          {bloodGroups.map((g) => (
            <option key={g.id} value={g.id}>
              {g.name}
            </option>
          ))}
        </FormField>
        <FormField label="Units required" id="units_required" type="number" min={1} max={100} value={form.units_required} onChange={handleChange} required />
      </div>
      <FormField label="Urgency" id="urgency" as="select" value={form.urgency} onChange={handleChange}>
        <option value="normal">Normal</option>
        <option value="urgent">Urgent</option>
        <option value="critical">Critical</option>
      </FormField>
      <FormField label="Location (hospital / city)" id="location" value={form.location} onChange={handleChange} required />
      <FormField label="Notes" id="notes" as="textarea" rows={3} value={form.notes} onChange={handleChange} />
      <div className="flex gap-2">
        <Button type="submit" disabled={saving}>
          {saving ? 'Saving...' : isEdit ? 'Save changes' : 'Submit request'}
        </Button>
        <Button variant="secondary" onClick={() => navigate(isEdit ? `${base}/${id}` : base)}>
          Cancel
        </Button>
      </div>
    </form>
  )
}

export default RequestForm
