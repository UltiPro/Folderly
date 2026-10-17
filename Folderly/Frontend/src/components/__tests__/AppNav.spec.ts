import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createMemoryHistory, createRouter } from 'vue-router'

import AppNav from '../AppNav.vue'
import { useAuthStore } from '@/stores/auth'

vi.hoisted(() => {
  globalThis.matchMedia = (() => ({
    matches: false,
    addEventListener: () => {},
    removeEventListener: () => {},
  })) as unknown as typeof globalThis.matchMedia
})

const blank = { template: '<div />' }

async function highlighted(to: string): Promise<string> {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/files', name: 'files', component: blank },
      { path: '/shared', name: 'shared', component: blank },
      { path: '/account', name: 'account', component: blank },
      { path: '/activate', name: 'activate', component: blank },
      { path: '/login', name: 'login', component: blank },
    ],
  })
  router.push(to)
  await router.isReady()

  const wrapper = mount(AppNav, { global: { plugins: [router] } })
  return wrapper
    .findAll('a')
    .filter((link) => link.classes().includes('bg-surface-sunken'))
    .map((link) => link.text())
    .join(' | ')
}

describe('AppNav', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    useAuthStore().user = { email: 'demo@folderly.app', active: true }
  })

  it('highlights My files in your own space', async () => {
    const active = await highlighted('/files?path=/Photos')
    expect(active).toContain('My files')
    expect(active).not.toContain('Shared with me')
  })

  it('highlights Shared with me inside a folder someone shared', async () => {
    const active = await highlighted('/files?path=/&share=Kx8vN2qLmT4')
    expect(active).toContain('Shared with me')
    expect(active).not.toContain('My files')
  })

  it('highlights Shared with me on the list of shared folders', async () => {
    expect(await highlighted('/shared')).toContain('Shared with me')
  })
})
