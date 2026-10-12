import { http } from './client'
import type { AuthTokens, UserInfo } from '@/types/api'

export async function register(email: string, password: string): Promise<void> {
  await http.post('/register', { email, password })
}

export async function login(email: string, password: string): Promise<AuthTokens> {
  const { data } = await http.post<AuthTokens>('/login', { email, password })
  return data
}

export async function logout(): Promise<void> {
  await http.post('/logout')
}

export async function fetchCurrentUser(): Promise<UserInfo> {
  const { data } = await http.get<UserInfo>('/user')
  return data
}

export async function activate(code: string): Promise<void> {
  await http.post('/user/activate', { code })
}

export async function updateAccount(
  email: string,
  password: string,
  currentPassword: string,
): Promise<AuthTokens> {
  const { data } = await http.put<AuthTokens>('/user', {
    email,
    password,
    current_password: currentPassword,
  })
  return data
}

export async function deleteAccount(currentPassword: string): Promise<void> {
  await http.delete('/user', { data: { current_password: currentPassword } })
}
