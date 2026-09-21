const colors = {
  pending: 'bg-yellow-100 text-yellow-800',
  approved: 'bg-blue-100 text-blue-800',
  matched: 'bg-indigo-100 text-indigo-800',
  processing: 'bg-purple-100 text-purple-800',
  completed: 'bg-green-100 text-green-800',
  scheduled: 'bg-blue-100 text-blue-800',
  cancelled: 'bg-gray-200 text-gray-700',
  rejected: 'bg-red-100 text-red-800',
  verified: 'bg-green-100 text-green-800',
  unverified: 'bg-yellow-100 text-yellow-800',
  normal: 'bg-gray-100 text-gray-700',
  urgent: 'bg-orange-100 text-orange-800',
  critical: 'bg-red-100 text-red-800',
}

function StatusBadge({ value }) {
  return (
    <span
      className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium capitalize ${colors[value] ?? 'bg-gray-100 text-gray-700'}`}
    >
      {value}
    </span>
  )
}

export default StatusBadge
