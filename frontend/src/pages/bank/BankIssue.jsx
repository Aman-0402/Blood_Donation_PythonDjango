import { useState } from 'react'
import Alert from '../../components/Alert'
import Button from '../../components/Button'
import FormField from '../../components/FormField'
import { useBloodGroups } from '../../hooks/useBloodGroups'
import { issueUnits } from '../../services/inventory'
import { extractError } from '../../utils/errors'

function BankIssue() {
  const bloodGroups = useBloodGroups()
  const [form, setForm] = useState({ blood_group: '', units: 1, note: '' })
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [saving, setSaving] = useState(false)

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setMessage('')
    setSaving(true)
    try {
      const res = await issueUnits({ ...form, blood_group: Number(form.blood_group), units: Number(form.units) })
      setMessage(`Issued ${res.issued} unit(s) of ${res.blood_group} (oldest expiry first).`)
      setForm({ blood_group: '', units: 1, note: '' })
    } catch (err) {
      setError(extractError(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="max-w-xl space-y-4">
      <h1 className="text-2xl font-semibold text-gray-900">Issue blood</h1>
      <p className="text-sm text-gray-600">
        Use this for direct dispatches. Blood for a patient request is issued from the request page.
      </p>
      <Alert type="error">{error}</Alert>
      <Alert type="success">{message}</Alert>
      <FormField label="Blood group" id="blood_group" as="select" value={form.blood_group} onChange={handleChange} required>
        <option value="">Select...</option>
        {bloodGroups.map((g) => (
          <option key={g.id} value={g.id}>
            {g.name}
          </option>
        ))}
      </FormField>
      <FormField label="Units" id="units" type="number" min={1} max={1000} value={form.units} onChange={handleChange} required />
      <FormField label="Recipient / note" id="note" value={form.note} onChange={handleChange} />
      <Button type="submit" disabled={saving}>
        {saving ? 'Issuing...' : 'Issue blood'}
      </Button>
    </form>
  )
}

export default BankIssue
