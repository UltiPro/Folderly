import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'

import ShareDialog from '../ShareDialog.vue'
import * as foldersApi from '@/api/folders'
import type { FolderMember, Role, SpacePath } from '@/types/api'

vi.mock('@/api/folders', () => ({
  listMembers: vi.fn<(path: SpacePath) => Promise<FolderMember[]>>(),
  shareFolder: vi.fn<(path: SpacePath, email: string, role: Role) => Promise<void>>(),
  revokeShare: vi.fn<(path: SpacePath, email: string) => Promise<void>>(),
}))

describe('ShareDialog', () => {
  beforeEach(() => {
    vi.mocked(foldersApi.listMembers).mockReset()
    vi.mocked(foldersApi.listMembers).mockResolvedValue([
      { email: 'ada@example.com', role: 'edit' },
    ])
  })

  afterEach(() => {
    document.body.innerHTML = ''
  })

  it('asks who already has access when it is created already open', async () => {
    const wrapper = mount(ShareDialog, { props: { open: true, path: '/Photos' } })
    await flushPromises()

    expect(foldersApi.listMembers).toHaveBeenCalledWith('/Photos')
    expect(document.body.textContent).toContain('ada@example.com')
    wrapper.unmount()
  })

  it('asks again when a mounted dialog is reopened', async () => {
    const wrapper = mount(ShareDialog, { props: { open: false, path: '/Photos' } })
    await flushPromises()
    expect(foldersApi.listMembers).not.toHaveBeenCalled()

    await wrapper.setProps({ open: true })
    await flushPromises()
    expect(foldersApi.listMembers).toHaveBeenCalledTimes(1)
    wrapper.unmount()
  })
})
