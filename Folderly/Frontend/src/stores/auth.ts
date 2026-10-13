import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import * as authApi from '@/api/auth'
import { clearTokens, getAccessToken, setTokens } from '@/api/client'
import type { UserInfo } from '@/types/api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<UserInfo | null>(null)
  // True while the stored token is being checked, so guards can wait it out.
  const restoring = ref(false)

  const isAuthenticated = computed(() => user.value !== null)

  const isActive = computed(() => user.value?.active === true)

  async function login(email: string, password: string): Promise<void> {
    setTokens(await authApi.login(email, password))
    user.value = await authApi.fetchCurrentUser()
  }

  async function register(email: string, password: string): Promise<void> {
    await authApi.register(email, password)
    // Registration leaves the account inactive, signing in straight away lets
    // the router take them to the activation screen instead of the login form.
    await login(email, password)
  }

  async function logout(): Promise<void> {
    try {
      // Revokes the token server-side, a failure here still logs the user out
      // locally, which is what they asked for.
      await authApi.logout()
    } catch {
    } finally {
      forget()
    }
  }

  function forget(): void {
    clearTokens()
    user.value = null
  }

  async function restore(): Promise<void> {
    if (user.value || !getAccessToken()) return

    restoring.value = true
    try {
      user.value = await authApi.fetchCurrentUser()
    } catch {
      forget()
    } finally {
      restoring.value = false
    }
  }

  async function activate(code: string): Promise<void> {
    await authApi.activate(code)
    user.value = await authApi.fetchCurrentUser()
  }

  // The new tokens have to be stored, this session is logged out too.
  async function updateAccount(
    email: string,
    password: string,
    currentPassword: string,
  ): Promise<void> {
    setTokens(await authApi.updateAccount(email, password, currentPassword))
    user.value = await authApi.fetchCurrentUser()
  }

  async function deleteAccount(currentPassword: string): Promise<void> {
    await authApi.deleteAccount(currentPassword)
    forget()
  }

  return {
    user,
    restoring,
    isAuthenticated,
    isActive,
    login,
    register,
    logout,
    forget,
    restore,
    activate,
    updateAccount,
    deleteAccount,
  }
})
