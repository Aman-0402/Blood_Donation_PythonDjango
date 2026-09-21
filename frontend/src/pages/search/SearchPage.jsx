import { useState } from 'react'
import Alert from '../../components/Alert'
import Button from '../../components/Button'
import FormField from '../../components/FormField'
import { useBloodGroups } from '../../hooks/useBloodGroups'
import { searchBlood, searchDonors, searchHospitals } from '../../services/search'
import { extractError } from '../../utils/errors'

const TABS = [
  { key: 'blood', label: 'Blood availability' },
  { key: 'donors', label: 'Donors' },
  { key: 'hospitals', label: 'Hospitals' },
]

function ResultTable({ columns, rows, empty }) {
  if (rows.length === 0) return <p className="text-sm text-gray-500">{empty}</p>
  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white">
      <table className="min-w-full text-left text-sm">
        <thead className="bg-gray-50 text-gray-600">
          <tr>
            {columns.map((c) => (
              <th key={c.label} className="px-4 py-2 font-medium">
                {c.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {rows.map((row, i) => (
            <tr key={row.key ?? i}>
              {columns.map((c) => (
                <td key={c.label} className="px-4 py-2">
                  {c.render(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

const bloodColumns = [
  { label: 'Blood bank', render: (r) => r.bloodbank_name },
  { label: 'City', render: (r) => r.city },
  { label: 'Address', render: (r) => r.address || '-' },
  {
    label: 'Blood group',
    render: (r) => (
      <span>
        {r.blood_group_name}
        {!r.exact && <span className="ml-1 text-xs text-gray-500">(compatible)</span>}
      </span>
    ),
  },
  { label: 'Units available', render: (r) => r.units_available },
]

const donorColumns = [
  { label: 'City', render: (r) => r.city },
  { label: 'Blood group', render: (r) => r.blood_group_name },
  { label: 'Eligible donors (approx.)', render: (r) => r.available_donors },
]

const hospitalColumns = [
  { label: 'Hospital', render: (r) => r.name },
  { label: 'City', render: (r) => r.city },
  { label: 'Address', render: (r) => r.address || '-' },
]

function SearchPage() {
  const bloodGroups = useBloodGroups()
  const [tab, setTab] = useState('blood')
  const [form, setForm] = useState({ blood_group: '', compatible: false, city: '', bank_name: '', min_units: '', name: '' })
  const [results, setResults] = useState({})
  const [error, setError] = useState('')
  const [searching, setSearching] = useState(false)

  const handleChange = (e) => {
    const { name, type, value, checked } = e.target
    setForm({ ...form, [name]: type === 'checkbox' ? checked : value })
  }

  const buildParams = () => {
    const params = {}
    if (tab !== 'hospitals') {
      if (form.blood_group) params.blood_group = form.blood_group
      if (form.compatible) params.compatible = true
    }
    if (form.city.trim()) params.city = form.city.trim()
    if (tab === 'blood') {
      if (form.bank_name.trim()) params.bank_name = form.bank_name.trim()
      if (form.min_units) params.min_units = form.min_units
    }
    if (tab === 'hospitals' && form.name.trim()) params.name = form.name.trim()
    return params
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSearching(true)
    const search = { blood: searchBlood, donors: searchDonors, hospitals: searchHospitals }[tab]
    try {
      const rows = await search(buildParams())
      setResults({ ...results, [tab]: rows })
    } catch (err) {
      setError(extractError(err))
    } finally {
      setSearching(false)
    }
  }

  const rows = results[tab]

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold text-gray-900">Search</h1>
      <div role="tablist" className="flex gap-2 border-b border-gray-200">
        {TABS.map((t) => (
          <button
            key={t.key}
            type="button"
            role="tab"
            aria-selected={tab === t.key}
            onClick={() => {
              setTab(t.key)
              setError('')
            }}
            className={`-mb-px border-b-2 px-3 py-2 text-sm font-medium ${
              tab === t.key ? 'border-red-600 text-red-700' : 'border-transparent text-gray-600 hover:text-gray-900'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-3">
        {tab !== 'hospitals' && (
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
        )}
        <div className="w-44">
          <FormField label="City" id="city" value={form.city} onChange={handleChange} />
        </div>
        {tab === 'blood' && (
          <>
            <div className="w-48">
              <FormField label="Blood bank name" id="bank_name" value={form.bank_name} onChange={handleChange} />
            </div>
            <div className="w-32">
              <FormField label="Min. units" id="min_units" type="number" min={1} value={form.min_units} onChange={handleChange} />
            </div>
          </>
        )}
        {tab === 'hospitals' && (
          <div className="w-48">
            <FormField label="Hospital name" id="name" value={form.name} onChange={handleChange} />
          </div>
        )}
        {tab !== 'hospitals' && (
          <label className="flex items-center gap-2 pb-2 text-sm text-gray-700">
            <input type="checkbox" name="compatible" checked={form.compatible} onChange={handleChange} />
            Include compatible groups
          </label>
        )}
        <Button type="submit" disabled={searching}>
          {searching ? 'Searching...' : 'Search'}
        </Button>
      </form>

      {tab === 'donors' && (
        <p className="text-xs text-gray-500">
          Donor counts are approximate and never identify individuals. To reach donors, create a blood request; donors who accept share their contact details with you.
        </p>
      )}
      <Alert type="error">{error}</Alert>
      {rows && tab === 'blood' && (
        <ResultTable columns={bloodColumns} rows={rows.map((r) => ({ ...r, key: `${r.bloodbank}-${r.blood_group}` }))} empty="No matching blood available." />
      )}
      {rows && tab === 'donors' && (
        <ResultTable columns={donorColumns} rows={rows.map((r) => ({ ...r, key: `${r.city}-${r.blood_group_name}` }))} empty="No eligible donors found." />
      )}
      {rows && tab === 'hospitals' && (
        <ResultTable columns={hospitalColumns} rows={rows.map((r) => ({ ...r, key: r.id }))} empty="No hospitals found." />
      )}
    </div>
  )
}

export default SearchPage
