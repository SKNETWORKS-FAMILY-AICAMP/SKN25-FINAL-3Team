// FastAPI 엔드포인트 base URL
// 개발: '' (Vite proxy가 /api/* → FastAPI 처리)
// 운영: 'https://api.example.com'
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''

// Django 인증 엔드포인트 base URL
// 개발: '' (Vite proxy가 /auth/* → Django 처리, 경로에 /auth 접두어 포함)
// 운영: 'https://auth.example.com' (경로에서 /auth 접두어 제거)
const AUTH_BASE = import.meta.env.VITE_AUTH_BASE_URL ?? null

// /auth/api/auth/login/ 같은 경로를 환경에 맞게 변환합니다.
// 개발: 그대로 (Vite proxy가 /auth 접두어 인식)
// 운영: /auth 접두어 제거 후 AUTH_BASE 붙임
function resolveAuthUrl(path: string): string {
  if (AUTH_BASE) return `${AUTH_BASE}${path.replace(/^\/auth/, '')}`
  return path
}

function getAuthHeader(): Record<string, string> {
  const token = localStorage.getItem('access_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function tryRefresh(): Promise<boolean> {
  const refresh = localStorage.getItem('refresh_token')
  if (!refresh) return false
  try {
    const res = await fetch(resolveAuthUrl('/auth/api/auth/token/refresh/'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh }),
    })
    if (!res.ok) return false
    const data = await res.json()
    localStorage.setItem('access_token', data.access)
    return true
  } catch {
    return false
  }
}

async function request<T>(path: string, init?: RequestInit, retry = true): Promise<T> {
  const url = path.startsWith('/auth/') ? resolveAuthUrl(path) : `${API_BASE}${path}`
  const isFormData = typeof FormData !== 'undefined' && init?.body instanceof FormData
  const res = await fetch(url, {
    headers: {
      ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
      ...getAuthHeader(),
      ...init?.headers,
    },
    ...init,
  })

  if (res.status === 401 && retry) {
    const refreshed = await tryRefresh()
    if (refreshed) return request<T>(path, init, false)
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    window.location.href = '/login'
    throw new Error('Unauthorized')
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    // DRF 필드별 에러: { username: ["..."], age: ["..."] }
    if (err.detail) throw new Error(err.detail)
    if (err.error)  throw new Error(err.error)
    const fieldErrors = Object.entries(err as Record<string, unknown>)
      .flatMap(([field, msgs]) =>
        Array.isArray(msgs) ? (msgs as string[]).map(m => `${field}: ${m}`) : [`${field}: ${msgs}`]
      )
    if (fieldErrors.length) throw new Error(fieldErrors.join('\n'))
    throw new Error(`HTTP ${res.status}`)
  }

  return res.json() as Promise<T>
}

export const api = {
  get:    <T>(path: string)                => request<T>(path),
  post:   <T>(path: string, body: unknown) => request<T>(path, { method: 'POST',   body: JSON.stringify(body) }),
  postForm: <T>(path: string, body: FormData) => request<T>(path, { method: 'POST', body }),
  patch:  <T>(path: string, body: unknown) => request<T>(path, { method: 'PATCH',  body: JSON.stringify(body) }),
  delete: <T>(path: string)               => request<T>(path, { method: 'DELETE' }),
}
