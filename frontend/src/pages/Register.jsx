import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import Alert from '../components/Alert'
import Button from '../components/Button'
import FormField from '../components/FormField'
import { useAuth } from '../hooks/useAuth'
import { extractError } from '../utils/errors'
import { REGISTER_ROLES, roleHome } from '../utils/roles'

const initialForm = {
  username: '',
  email: '',
  password: '',
  first_name: '',
  last_name: '',
  phone: '',
  role: 'donor',
}

function Register() {
  const { user, register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState(initialForm)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  if (user) return <Navigate to={roleHome(user.role)} replace />

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      const me = await register(form)
      navigate(roleHome(me.role), { replace: true })
    } catch (err) {
      setError(extractError(err))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 p-4">
      <form onSubmit={handleSubmit} className="w-full max-w-md space-y-4 rounded-lg bg-white p-6 shadow">
        <h1 className="text-xl font-semibold text-gray-900">Create an account</h1>
        <Alert type="error">{error}</Alert>
        <FormField label="I am a" id="role" as="select" value={form.role} onChange={handleChange}>
          {REGISTER_ROLES.map((r) => (
            <option key={r.value} value={r.value}>
              {r.label}
            </option>
          ))}
        </FormField>
        <div className="grid grid-cols-2 gap-3">
          <FormField label="First name" id="first_name" value={form.first_name} onChange={handleChange} />
          <FormField label="Last name" id="last_name" value={form.last_name} onChange={handleChange} />
        </div>
        <FormField label="Username" id="username" value={form.username} onChange={handleChange} required autoComplete="username" />
        <FormField label="Email" id="email" type="email" value={form.email} onChange={handleChange} required autoComplete="email" />
        <FormField label="Phone" id="phone" type="tel" value={form.phone} onChange={handleChange} autoComplete="tel" />
        <FormField label="Password" id="password" type="password" value={form.password} onChange={handleChange} required autoComplete="new-password" minLength={8} />
        <Button type="submit" disabled={submitting} className="w-full">
          {submitting ? 'Creating account...' : 'Register'}
        </Button>
        <p className="text-center text-sm text-gray-600">
          Already registered?{' '}
          <Link to="/login" className="text-red-700 underline">
            Log in
          </Link>
        </p>
      </form>
    </div>
  )
}

export default Register
