import { useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import Button from '../components/Button'
import Container from '../components/Container'
import NotificationBell from '../components/NotificationBell'
import { useAuth } from '../hooks/useAuth'
import { NAV_ITEMS } from './navConfig'

const linkClass = ({ isActive }) =>
  `block rounded-md px-3 py-2 text-sm font-medium transition-colors ${
    isActive ? 'bg-red-50 text-red-700' : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
  }`

function DashboardLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const items = NAV_ITEMS[user.role] ?? []
  const [navOpen, setNavOpen] = useState(false)

  const handleLogout = async () => {
    await logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="sticky top-0 z-30 border-b border-gray-200 bg-white">
        <Container className="flex h-14 items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <button
              type="button"
              aria-label="Toggle navigation menu"
              aria-expanded={navOpen}
              onClick={() => setNavOpen((v) => !v)}
              className="rounded-md p-2 text-gray-600 hover:bg-gray-100 md:hidden"
            >
              <span aria-hidden="true">☰</span>
            </button>
            <span className="whitespace-nowrap font-semibold text-red-700">Blood Donation System</span>
          </div>
          <div className="flex items-center gap-1 sm:gap-3">
            <span className="hidden text-sm text-gray-600 sm:inline">
              {user.username} ({user.role})
            </span>
            <NotificationBell />
            <Button variant="secondary" onClick={handleLogout}>
              Logout
            </Button>
          </div>
        </Container>
      </header>

      <Container className="flex flex-col gap-6 py-4 md:flex-row md:items-start md:py-6">
        <nav
          aria-label="Main"
          className={`${navOpen ? 'block' : 'hidden'} rounded-lg border border-gray-200 bg-white p-2 md:sticky md:top-20 md:block md:w-56 md:shrink-0 md:border-0 md:bg-transparent md:p-0`}
        >
          <div className="flex flex-col gap-1">
            {items.map((item) => (
              <NavLink key={item.to} to={item.to} end={item.end} onClick={() => setNavOpen(false)} className={linkClass}>
                {item.label}
              </NavLink>
            ))}
          </div>
        </nav>
        <main className="min-w-0 flex-1">
          <Outlet />
        </main>
      </Container>
    </div>
  )
}

export default DashboardLayout
