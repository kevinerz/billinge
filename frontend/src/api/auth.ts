import { apiClient, clearTokens, setTokens } from './client'
import type { Me } from './types'

export async function login(email: string, password: string): Promise<void> {
  const { data } = await apiClient.post('/token/', { email, password })
  setTokens(data.access, data.refresh)
}

export async function fetchMe(): Promise<Me> {
  const { data } = await apiClient.get('/me/')
  return data
}

export function logout(): void {
  clearTokens()
}
