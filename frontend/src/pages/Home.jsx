import { useEffect, useState } from 'react'
import api from '../services/api'

function Home() {
  const [status, setStatus] = useState('checking...')

  useEffect(() => {
    api
      .get('/health/')
      .then((res) => setStatus(res.data.status))
      .catch(() => setStatus('unreachable'))
  }, [])

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-3xl font-semibold text-gray-900">
          Blood Donation Management System
        </h1>
        <p className="mt-2 text-gray-500">Backend API status: {status}</p>
      </div>
    </div>
  )
}

export default Home
