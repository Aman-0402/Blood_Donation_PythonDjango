import { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import Alert from '../components/Alert'
import Button from '../components/Button'
import FormField from '../components/FormField'
import { useAuth } from '../hooks/useAuth'
import { extractError } from '../utils/errors'
import { roleHome } from '../utils/roles'

function Login() {
  const { user, login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [form, setForm] = useState({ username: '', password: '' })
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  if (user) return <Navigate to={roleHome(user.role)} replace />

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      const me = await login(form.username, form.password)
      const target = location.state?.from?.pathname
      navigate(target?.startsWith(roleHome(me.role)) ? target : roleHome(me.role), { replace: true })
    } catch (err) {
      setError(
        err.response?.status === 401
          ? 'Invalid username or password.'
          : extractError(err),
      )
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 p-4">
      <form onSubmit={handleSubmit} className="w-full max-w-sm space-y-4 rounded-lg bg-white p-6 shadow">
        <h1 className="text-xl font-semibold text-gray-900">Log in</h1>
        <Alert type="error">{error}</Alert>
        <FormField label="Username" id="username" value={form.username} onChange={handleChange} required autoComplete="username" />
        <FormField label="Password" id="password" type="password" value={form.password} onChange={handleChange} required autoComplete="current-password" />
        <Button type="submit" disabled={submitting} className="w-full">
          {submitting ? 'Logging in...' : 'Log in'}
        </Button>
        <p className="text-center text-sm text-gray-600">
          No account?{' '}
          <Link to="/register" className="text-red-700 underline">
            Register
          </Link>
        </p>
      </form>
    </div>
  )
}

export default Login
