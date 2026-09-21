import { useEffect, useState } from 'react'
import { getBloodGroups } from '../services/reference'

export function useBloodGroups() {
  const [bloodGroups, setBloodGroups] = useState([])

  useEffect(() => {
    let active = true
    getBloodGroups()
      .then((groups) => active && setBloodGroups(groups))
      .catch(() => {})
    return () => {
      active = false
    }
  }, [])

  return bloodGroups
}
