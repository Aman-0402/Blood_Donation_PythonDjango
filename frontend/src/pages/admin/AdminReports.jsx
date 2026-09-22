import { useEffect, useState } from 'react'
import Alert from '../../components/Alert'
import StatCard from '../../components/StatCard'
import BarChart from '../../components/charts/BarChart'
import LineChart from '../../components/charts/LineChart'
import { getDonationReport, getInventoryReport, getRequestReport } from '../../services/reports'
import { extractError } from '../../utils/errors'

function AdminReports() {
  const [donations, setDonations] = useState(null)
  const [requests, setRequests] = useState(null)
  const [inventory, setInventory] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true
    Promise.all([getDonationReport(), getRequestReport(), getInventoryReport()])
      .then(([d, r, i]) => {
        if (!active) return
        setDonations(d)
        setRequests(r)
        setInventory(i)
      })
      .catch((err) => active && setError(extractError(err)))
      .finally(() => active && setLoading(false))
    return () => {
      active = false
    }
  }, [])

  if (loading) return <p className="text-gray-500">Loading...</p>
  if (error) return <Alert type="error">{error}</Alert>

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-semibold text-gray-900">Reports</h1>

      <section className="space-y-4">
        <h2 className="text-lg font-medium text-gray-900">Donations</h2>
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          <StatCard label="Units collected (all time)" value={donations.total_units_collected} />
          <StatCard label="Completed" value={donations.by_status.completed} />
          <StatCard label="Scheduled" value={donations.by_status.scheduled} />
          <StatCard label="Cancelled / rejected" value={donations.by_status.cancelled + donations.by_status.rejected} />
        </div>
        <div className="grid gap-6 lg:grid-cols-2">
          <div className="rounded-lg border border-gray-200 bg-white p-4">
            <BarChart
              title="Completed donations by blood group"
              data={donations.by_blood_group.map((r) => ({ label: r.blood_group_name, value: r.count }))}
            />
          </div>
          <div className="rounded-lg border border-gray-200 bg-white p-4">
            <LineChart
              title="Units collected per month (last 12 months)"
              data={donations.monthly.map((m) => ({ label: m.month.slice(2), value: m.units }))}
            />
          </div>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="text-lg font-medium text-gray-900">Blood requests</h2>
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          <StatCard label="Total requests" value={requests.total_requests} />
          <StatCard label="Completion rate" value={`${requests.completion_rate}%`} />
          <StatCard
            label="Avg. fulfilment time"
            value={requests.avg_fulfillment_hours != null ? `${requests.avg_fulfillment_hours}h` : '—'}
          />
          <StatCard label="Closed requests" value={requests.closed_requests} />
        </div>
        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <BarChart
            title="Requests by blood group"
            data={requests.by_blood_group.map((r) => ({ label: r.blood_group_name, value: r.count }))}
          />
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="text-lg font-medium text-gray-900">Blood inventory</h2>
        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <BarChart
            title="Usable stock by blood group (all banks)"
            data={inventory.by_blood_group.map((r) => ({ label: r.blood_group_name, value: r.units_available }))}
          />
        </div>
        {inventory.expiring_within_7_days.length > 0 && (
          <Alert type="info">
            Expiring within 7 days:{' '}
            {inventory.expiring_within_7_days.map((r) => `${r.blood_group_name} (${r.units})`).join(', ')}
          </Alert>
        )}
      </section>
    </div>
  )
}

export default AdminReports
