import Alert from '../components/Alert'
import { useAuth } from '../hooks/useAuth'

function RoleHome() {
  const { user } = useAuth()
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold text-gray-900">Welcome, {user.first_name || user.username}</h1>
      {!user.is_verified && (
        <Alert type="info">Your account is awaiting verification by an administrator.</Alert>
      )}
    </div>
  )
}

export default RoleHome
