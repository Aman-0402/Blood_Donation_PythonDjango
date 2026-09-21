import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import Button from '../components/Button'
import { useAuth } from '../hooks/useAuth'
import { NAV_ITEMS } from './navConfig'

const linkClass = ({ isActive }) =>
  `block rounded-md px-3 py-2 text-sm font-medium ${
    isActive ? 'bg-red-50 text-red-700' : 'text-gray-600 hover:bg-gray-100'
  }`

function DashboardLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const items = NAV_ITEMS[user.role] ?? []

  const handleLogout = async () => {
    await logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="flex items-center justify-between border-b border-gray-200 bg-white px-4 py-3">
        <span className="font-semibold text-red-700">Blood Donation System</span>
        <div className="flex items-center gap-3">
          <span className="hidden text-sm text-gray-600 sm:inline">
            {user.username} ({user.role})
          </span>
          <Button variant="secondary" onClick={handleLogout}>
            Logout
          </Button>
        </div>
      </header>
      <div className="mx-auto flex max-w-6xl flex-col gap-4 p-4 md:flex-row">
        <nav aria-label="Main" className="flex gap-1 md:w-48 md:flex-col">
          {items.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.end} className={linkClass}>
              {item.label}
            </NavLink>
          ))}
        </nav>
        <main className="min-w-0 flex-1">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export default DashboardLayout
