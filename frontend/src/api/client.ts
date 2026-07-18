import axios, { type InternalAxiosRequestConfig } from 'axios'

const baseURL = import.meta.env.VITE_API_BASE_URL

export const apiClient = axios.create({ baseURL })

const ACCESS_KEY = 'billinge_access_token'
const REFRESH_KEY = 'billinge_refresh_token'

export function getAccessToken() {
  return localStorage.getItem(ACCESS_KEY)
}
export function getRefreshToken() {
  return localStorage.getItem(REFRESH_KEY)
}
export function setTokens(access: string, refresh?: string) {
  localStorage.setItem(ACCESS_KEY, access)
  if (refresh) localStorage.setItem(REFRESH_KEY, refresh)
}
export function clearTokens() {
  localStorage.removeItem(ACCESS_KEY)
  localStorage.removeItem(REFRESH_KEY)
}

apiClient.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) {
    config.headers.set('Authorization', `Bearer ${token}`)
  }
  return config
})

let refreshPromise: Promise<string> | null = null

async function refreshAccessToken(): Promise<string> {
  const refresh = getRefreshToken()
  if (!refresh) throw new Error('No refresh token')
  const { data } = await axios.post(`${baseURL}/token/refresh/`, { refresh })
  setTokens(data.access)
  return data.access as string
}

interface RetryableConfig extends InternalAxiosRequestConfig {
  _retry?: boolean
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config as RetryableConfig | undefined
    if (
      error.response?.status === 401 &&
      originalRequest &&
      !originalRequest._retry &&
      getRefreshToken()
    ) {
      originalRequest._retry = true
      try {
        if (!refreshPromise) {
          refreshPromise = refreshAccessToken().finally(() => {
            refreshPromise = null
          })
        }
        const newToken = await refreshPromise
        originalRequest.headers.set('Authorization', `Bearer ${newToken}`)
        return apiClient(originalRequest)
      } catch (refreshError) {
        clearTokens()
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }
    return Promise.reject(error)
  },
)
