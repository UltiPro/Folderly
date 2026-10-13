import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'

import PreviewDialog from '../PreviewDialog.vue'
import * as filesApi from '@/api/files'
import type { FileEntry, ShareToken, SpacePath } from '@/types/api'

vi.mock('@/api/files', () => ({
  fetchFileBlob: vi.fn<(path: SpacePath, filename: string, share?: ShareToken) => Promise<Blob>>(),
}))

function entry(name: string, extension: string, size = 100): FileEntry {
  return { name, type: 'file', extension, size }
}

function open(file: FileEntry) {
  return mount(PreviewDialog, {
    props: { open: true, entry: file, path: '/' as SpacePath, share: null },
  })
}

describe('PreviewDialog', () => {
  beforeEach(() => {
    vi.mocked(filesApi.fetchFileBlob).mockReset()
    URL.createObjectURL = vi.fn<(obj: Blob | MediaSource) => string>(() => 'blob:stub')
    URL.revokeObjectURL = vi.fn<(url: string) => void>()
  })

  afterEach(() => {
    document.body.innerHTML = ''
  })

  it('shows a text file without turning it into a document', async () => {
    vi.mocked(filesApi.fetchFileBlob).mockResolvedValue(new Blob(['pierwsza linia\ndruga']))

    const wrapper = open(entry('notes.txt', 'txt'))
    await flushPromises()

    expect(filesApi.fetchFileBlob).toHaveBeenCalledWith('/', 'notes.txt', null)
    expect(document.body.textContent).toContain('pierwsza linia')
    expect(document.body.textContent).toContain('druga')
    expect(document.querySelector('pre')).not.toBeNull()
    expect(URL.createObjectURL).not.toHaveBeenCalled()
    wrapper.unmount()
  })

  it('shows markup as its own source rather than rendering it', async () => {
    const source = '<b>bold</b><script>globalThis.pwned = true</script>'
    vi.mocked(filesApi.fetchFileBlob).mockResolvedValue(new Blob([source]))

    const wrapper = open(entry('pwn.html', 'html'))
    await flushPromises()

    expect(document.querySelector('pre')?.textContent).toBe(source)
    expect(document.querySelector('pre b')).toBeNull()
    expect(document.querySelector('pre script')).toBeNull()
    wrapper.unmount()
  })

  it('reads an empty file as empty instead of unshowable', async () => {
    vi.mocked(filesApi.fetchFileBlob).mockResolvedValue(new Blob([]))

    const wrapper = open(entry('empty.log', 'log'))
    await flushPromises()

    expect(document.querySelector('pre')?.textContent).toBe('')
    expect(document.body.textContent).not.toContain('cannot be shown')
    wrapper.unmount()
  })

  it('says plainly when it cannot show a file at all', async () => {
    const wrapper = open(entry('sheet.xlsx', 'xlsx'))
    await flushPromises()

    expect(document.body.textContent).toContain('cannot be shown')
    wrapper.unmount()
  })

  it('leaves a text file past its own limit to Download', async () => {
    const huge = entry('huge.log', 'log', 5 * 1024 * 1024)

    const wrapper = open(huge)
    await flushPromises()

    expect(document.body.textContent).toContain('cannot be shown')
    wrapper.unmount()
  })
})
