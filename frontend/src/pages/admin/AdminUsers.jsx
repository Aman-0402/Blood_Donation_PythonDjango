import { useEffect, useState } from 'react'
import Alert from '../../components/Alert'
import Button from '../../components/Button'
import StatusBadge from '../../components/StatusBadge'
import { activateUser, deactivateUser, listUsers } from '../../services/admin'
import { extractError } from '../../utils/errors'
import { useAuth } from '../../hooks/useAuth'

const ROLES = ['admin', 'donor', 'seeker', 'hospital', 'bloodbank']

function AdminUsers() {
  const { user: me } = useAuth()
  const [role, setRole] = useState('')
  const [activeFilter, setActiveFilter] = useState('')
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [busyId, setBusyId] = useState(null)
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    let active = true
    const params = { page }
    if (role) params.role = role
    if (activeFilter) params.is_active = activeFilter
    if (search.trim()) params.search = search.trim()
    listUsers(params)
      .then((res) => active && setData(res))
      .catch((err) => active && setError(extractError(err)))
      .finally(() => active && setLoading(false))
    return () => {
      active = false
    }
  }, [page, role, activeFilter, search, reloadKey])

  const resetToPageOne = (setter) => (e) => {
    setLoading(true)
    setPage(1)
    setter(e.target.value)
  }

  const toggle = async (target) => {
    setError('')
    setBusyId(target.id)
    try {
      if (target.is_active) await deactivateUser(target.id)
      else await activateUser(target.id)
      setReloadKey((k) => k + 1)
    } catch (err) {
      setError(extractError(err))
    } finally {
      setBusyId(null)
    }
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold text-gray-900">Users</h1>
      <Alert type="error">{error}</Alert>
      <div className="flex flex-wrap items-end gap-3">
        <div>
          <label htmlFor="role-filter" className="mr-2 text-sm text-gray-600">
            Role
          </label>
          <select id="role-filter" value={role} onChange={resetToPageOne(setRole)} className="rounded-md border border-gray-300 px-2 py-1 text-sm">
            <option value="">All</option>
            {ROLES.map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="active-filter" className="mr-2 text-sm text-gray-600">
            Status
          </label>
          <select id="active-filter" value={activeFilter} onChange={resetToPageOne(setActiveFilter)} className="rounded-md border border-gray-300 px-2 py-1 text-sm">
            <option value="">All</option>
            <option value="true">Active</option>
            <option value="false">Deactivated</option>
          </select>
        </div>
        <div>
          <label htmlFor="user-search" className="mr-2 text-sm text-gray-600">
            Username
          </label>
          <input
            id="user-search"
            value={search}
            onChange={resetToPageOne(setSearch)}
            className="rounded-md border border-gray-300 px-2 py-1 text-sm"
          />
        </div>
      </div>
      {loading && !data ? (
        <p className="text-gray-500">Loading...</p>
      ) : data && data.results.length === 0 ? (
        <p className="text-sm text-gray-500">No users found.</p>
      ) : (
        data && (
          <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white">
            <table className="min-w-full text-left text-sm">
              <thead className="bg-gray-50 text-gray-600">
                <tr>
                  <th className="px-4 py-2 font-medium">Username</th>
                  <th className="px-4 py-2 font-medium">Email</th>
                  <th className="px-4 py-2 font-medium">Role</th>
                  <th className="px-4 py-2 font-medium">Verified</th>
                  <th className="px-4 py-2 font-medium">Status</th>
                  <th className="px-4 py-2 font-medium" />
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {data.results.map((u) => (
                  <tr key={u.id}>
                    <td className="px-4 py-2">{u.username}</td>
                    <td className="px-4 py-2">{u.email}</td>
                    <td className="px-4 py-2 capitalize">{u.role}</td>
                    <td className="px-4 py-2">{u.is_verified ? 'Yes' : 'No'}</td>
                    <td className="px-4 py-2">
                      <StatusBadge value={u.is_active ? 'verified' : 'unverified'} />
                    </td>
                    <td className="px-4 py-2 text-right">
                      {u.id !== me.id && u.role !== 'admin' && (
                        <Button
                          variant={u.is_active ? 'danger' : 'primary'}
                          disabled={busyId === u.id}
                          onClick={() => toggle(u)}
                        >
                          {u.is_active ? 'Deactivate' : 'Activate'}
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      )}
      {data && (
        <div className="flex gap-2">
          <Button variant="secondary" disabled={!data.previous || loading} onClick={() => { setLoading(true); setPage(page - 1) }}>
            Previous
          </Button>
          <Button variant="secondary" disabled={!data.next || loading} onClick={() => { setLoading(true); setPage(page + 1) }}>
            Next
          </Button>
        </div>
      )}
    </div>
  )
}

export default AdminUsers
