import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { roleHome } from '../utils/roles'

function ProtectedRoute({ roles }) {
  const { user, loading } = useAuth()
  const location = useLocation()

  if (loading) {
    return <p className="p-8 text-center text-gray-500">Loading...</p>
  }
  if (!user) {
    return <Navigate to="/login" replace state={{ from: location }} />
  }
  if (roles && !roles.includes(user.role)) {
    return <Navigate to={roleHome(user.role)} replace />
  }
  return <Outlet />
}

export default ProtectedRoute
