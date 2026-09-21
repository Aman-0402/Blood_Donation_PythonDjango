import { useEffect, useState } from 'react'
import Alert from './Alert'
import { getRequestMatches, getRequestResponses } from '../services/search'
import { extractError } from '../utils/errors'

function MatchPanel({ requestId }) {
  const [matches, setMatches] = useState(null)
  const [offers, setOffers] = useState([])
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    Promise.all([getRequestMatches(requestId), getRequestResponses(requestId)])
      .then(([m, o]) => {
        if (!active) return
        setMatches(m)
        setOffers(o)
      })
      .catch((err) => active && setError(extractError(err)))
    return () => {
      active = false
    }
  }, [requestId])

  if (error) return <Alert type="error">{error}</Alert>
  if (!matches) return null

  return (
    <section className="space-y-4">
      <h2 className="text-lg font-medium text-gray-900">Matches{matches.city ? ` in ${matches.city}` : ''}</h2>
      <p className="text-sm text-gray-600">
        {matches.exact_stock_units} unit(s) of the exact group and {matches.compatible_stock_units} compatible unit(s) in stock at verified blood banks. About {matches.available_donors} eligible donor(s) could help.
      </p>

      {matches.blood_banks.length > 0 && (
        <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-gray-50 text-gray-600">
              <tr>
                <th className="px-4 py-2 font-medium">Blood bank</th>
                <th className="px-4 py-2 font-medium">City</th>
                <th className="px-4 py-2 font-medium">Group</th>
                <th className="px-4 py-2 font-medium">Units</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {matches.blood_banks.map((b) => (
                <tr key={`${b.bloodbank}-${b.blood_group}`}>
                  <td className="px-4 py-2">{b.bloodbank_name}</td>
                  <td className="px-4 py-2">{b.city}</td>
                  <td className="px-4 py-2">
                    {b.blood_group_name}
                    {!b.exact && <span className="ml-1 text-xs text-gray-500">(compatible)</span>}
                  </td>
                  <td className="px-4 py-2">{b.units_available}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div>
        <h3 className="mb-2 font-medium text-gray-900">Donors who offered to help ({offers.length})</h3>
        {offers.length === 0 ? (
          <p className="text-sm text-gray-500">No donor has accepted yet. Matching donors in your city can see this request.</p>
        ) : (
          <ul className="divide-y divide-gray-200 rounded-lg border border-gray-200 bg-white">
            {offers.map((o) => (
              <li key={o.id} className="flex flex-wrap items-center justify-between gap-2 px-4 py-3 text-sm">
                <span>
                  {o.donor_name} ({o.blood_group_name}, {o.city})
                </span>
                <a href={`tel:${o.donor_phone}`} className="text-red-700 underline">
                  {o.donor_phone || 'No phone provided'}
                </a>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  )
}

export default MatchPanel
