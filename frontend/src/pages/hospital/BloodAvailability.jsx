import { useState } from 'react'
import Alert from '../../components/Alert'
import Button from '../../components/Button'
import FormField from '../../components/FormField'
import { useBloodGroups } from '../../hooks/useBloodGroups'
import { searchBloodAvailability } from '../../services/hospitals'
import { extractError } from '../../utils/errors'

function BloodAvailability() {
  const bloodGroups = useBloodGroups()
  const [form, setForm] = useState({ blood_group: '', city: '' })
  const [results, setResults] = useState(null)
  const [error, setError] = useState('')
  const [searching, setSearching] = useState(false)

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSearching(true)
    const params = {}
    if (form.blood_group) params.blood_group = form.blood_group
    if (form.city.trim()) params.city = form.city.trim()
    try {
      setResults(await searchBloodAvailability(params))
    } catch (err) {
      setResults(null)
      setError(extractError(err))
    } finally {
      setSearching(false)
    }
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold text-gray-900">Blood availability</h1>
      <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-3">
        <div className="w-40">
          <FormField label="Blood group" id="blood_group" as="select" value={form.blood_group} onChange={handleChange}>
            <option value="">Any</option>
            {bloodGroups.map((g) => (
              <option key={g.id} value={g.id}>
                {g.name}
              </option>
            ))}
          </FormField>
        </div>
        <div className="w-48">
          <FormField label="City" id="city" value={form.city} onChange={handleChange} />
        </div>
        <Button type="submit" disabled={searching}>
          {searching ? 'Searching...' : 'Search'}
        </Button>
      </form>
      <Alert type="error">{error}</Alert>
      {results && results.length === 0 && <p className="text-sm text-gray-500">No matching blood available.</p>}
      {results && results.length > 0 && (
        <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-gray-50 text-gray-600">
              <tr>
                <th className="px-4 py-2 font-medium">Blood bank</th>
                <th className="px-4 py-2 font-medium">City</th>
                <th className="px-4 py-2 font-medium">Blood group</th>
                <th className="px-4 py-2 font-medium">Units available</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {results.map((r) => (
                <tr key={`${r.bloodbank_id}-${r.blood_group_id}`}>
                  <td className="px-4 py-2">{r.bloodbank__name}</td>
                  <td className="px-4 py-2">{r.bloodbank__city}</td>
                  <td className="px-4 py-2">{r.blood_group__name}</td>
                  <td className="px-4 py-2">{r.units_available}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export default BloodAvailability
