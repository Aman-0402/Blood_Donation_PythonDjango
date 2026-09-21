import { Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { roleHome } from '../utils/roles'

function Home() {
  const { user } = useAuth()
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 p-4">
      <div className="max-w-xl text-center">
        <h1 className="text-3xl font-semibold text-gray-900">Blood Donation Management System</h1>
        <p className="mt-2 text-gray-600">
          Connecting donors, patients, hospitals and blood banks.
        </p>
        <div className="mt-6 flex justify-center gap-3">
          {user ? (
            <Link to={roleHome(user.role)} className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700">
              Go to dashboard
            </Link>
          ) : (
            <>
              <Link to="/login" className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700">
                Log in
              </Link>
              <Link to="/register" className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50">
                Register
              </Link>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default Home
