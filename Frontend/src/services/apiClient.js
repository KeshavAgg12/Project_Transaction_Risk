// Single place that talks to the backend. Pages never call fetch directly.
export async function apiGet(path, params = {}) {
  const query = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== '' && value !== null && value !== undefined) query.set(key, value)
  })
  const suffix = query.toString() ? `?${query}` : ''

  const response = await fetch(`/api${path}${suffix}`)
  const body = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(body.error || `Request failed (${response.status})`)
  return body
}
