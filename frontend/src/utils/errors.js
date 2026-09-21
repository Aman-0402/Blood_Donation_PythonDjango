function flatten(value) {
  if (Array.isArray(value)) return value.flatMap(flatten)
  if (value && typeof value === 'object') return Object.values(value).flatMap(flatten)
  return [String(value)]
}

export function extractError(error, fallback = 'Something went wrong. Please try again.') {
  const data = error?.response?.data
  if (!data) {
    return error?.response ? fallback : 'Cannot reach the server. Please try again.'
  }
  if (typeof data === 'string') return fallback
  if (data.detail) return String(data.detail)
  const messages = Object.entries(data).flatMap(([field, value]) =>
    flatten(value).map((msg) => (field === 'non_field_errors' ? msg : `${field}: ${msg}`)),
  )
  return messages.length ? messages.join(' ') : fallback
}
