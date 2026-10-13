import axios, { AxiosError, type AxiosInstance, type InternalAxiosRequestConfig } from 'axios'

import type { ApiErrorBody } from '@/types/api'

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:5000'

export const http: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})

// Not in the store, the interceptors must reach it without importing Pinia.
const ACCESS_KEY = 'folderly.access_token'
const REFRESH_KEY = 'folderly.refresh_token'

let accessToken: string | null = localStorage.getItem(ACCESS_KEY)
let refreshToken: string | null = localStorage.getItem(REFRESH_KEY)

export function getAccessToken(): string | null {
  return accessToken
}

export function getRefreshToken(): string | null {
  return refreshToken
}

export function setTokens(tokens: { access_token: string; refresh_token?: string }): void {
  accessToken = tokens.access_token
  localStorage.setItem(ACCESS_KEY, tokens.access_token)
  if (tokens.refresh_token) {
    refreshToken = tokens.refresh_token
    localStorage.setItem(REFRESH_KEY, tokens.refresh_token)
  }
}

export function clearTokens(): void {
  accessToken = null
  refreshToken = null
  localStorage.removeItem(ACCESS_KEY)
  localStorage.removeItem(REFRESH_KEY)
}

let onSessionExpired: (() => void) | null = null

export function setSessionExpiredHandler(handler: () => void): void {
  onSessionExpired = handler
}

http.interceptors.request.use((config) => {
  // `/refresh` carries the refresh token instead, see refreshAccessToken below.
  if (accessToken && !config.headers.Authorization) {
    config.headers.Authorization = `Bearer ${accessToken}`
  }
  return config
})

// Here a 401 is about the credentials sent, so a retry is nonsense.
const CREDENTIAL_ENDPOINTS = ['/login', '/register', '/refresh']

function shouldRefresh(error: AxiosError, request: InternalAxiosRequestConfig): boolean {
  if (error.response?.status !== 401) return false
  const url = request.url ?? ''
  return !CREDENTIAL_ENDPOINTS.some((endpoint) => url.startsWith(endpoint))
}

// Shared across concurrent 401s so a burst of requests triggers one refresh.
let refreshInFlight: Promise<string> | null = null

async function refreshAccessToken(): Promise<string> {
  if (!refreshToken) throw new Error('No refresh token available.')

  refreshInFlight ??= axios
    .post<{ access_token: string }>('/refresh', null, {
      baseURL: API_BASE_URL,
      headers: { Authorization: `Bearer ${refreshToken}` },
    })
    .then((response) => {
      setTokens({ access_token: response.data.access_token })
      return response.data.access_token
    })
    .finally(() => {
      refreshInFlight = null
    })

  return refreshInFlight
}

type RetriableRequest = InternalAxiosRequestConfig & { _retried?: boolean }

http.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiErrorBody>) => {
    const request = error.config as RetriableRequest | undefined

    if (!request || request._retried || !shouldRefresh(error, request)) {
      return Promise.reject(error)
    }

    request._retried = true
    try {
      const token = await refreshAccessToken()
      request.headers.Authorization = `Bearer ${token}`
      return await http.request(request)
    } catch {
      clearTokens()
      onSessionExpired?.()
      return Promise.reject(error)
    }
  },
)

export function errorMessage(error: unknown, fallback = 'Something went wrong.'): string {
  if (!axios.isAxiosError(error)) return fallback

  const data = error.response?.data as ApiErrorBody | undefined
  const fields = data?.errors?.json ?? data?.errors?.query ?? data?.errors?.form
  if (fields) {
    const messages = Object.values(fields).flat()
    if (messages.length) return messages.join(' ')
  }

  if (data?.message) return data.message
  if (!error.response) return 'Cannot reach the server. Is the backend running?'
  return fallback
}

export function errorStatus(error: unknown): number | null {
  return axios.isAxiosError(error) ? (error.response?.status ?? null) : null
}

export function isNotActivated(error: unknown): boolean {
  if (errorStatus(error) !== 403) return false
  const data = axios.isAxiosError(error)
    ? (error.response?.data as ApiErrorBody | undefined)
    : undefined
  return data?.message?.includes('not activated') ?? false
}
