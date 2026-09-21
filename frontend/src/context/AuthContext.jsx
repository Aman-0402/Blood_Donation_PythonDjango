import { useCallback, useEffect, useMemo, useState } from 'react'
import * as authService from '../services/auth'
import { tokens } from '../services/tokens'
import { AuthContext } from './authContextValue'

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(Boolean(tokens.access))

  useEffect(() => {
    if (!tokens.access) return undefined
    let active = true
    authService
      .fetchMe()
      .then((me) => active && setUser(me))
      .catch(() => {
        tokens.clear()
      })
      .finally(() => active && setLoading(false))
    return () => {
      active = false
    }
  }, [])

  useEffect(() => {
    const onForcedLogout = () => setUser(null)
    window.addEventListener('auth:logout', onForcedLogout)
    return () => window.removeEventListener('auth:logout', onForcedLogout)
  }, [])

  const login = useCallback(async (username, password) => {
    const me = await authService.login(username, password)
    setUser(me)
    return me
  }, [])

  const register = useCallback(async (payload) => {
    const me = await authService.register(payload)
    setUser(me)
    return me
  }, [])

  const logout = useCallback(async () => {
    try {
      await authService.logout()
    } finally {
      setUser(null)
    }
  }, [])

  const value = useMemo(
    () => ({ user, loading, login, register, logout, setUser }),
    [user, loading, login, register, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
