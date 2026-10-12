import { describe, it, expect } from 'vitest'

import { formatExtension, formatSize, pluralize } from '../format'

describe('formatSize', () => {
  it('keeps plain bytes exact', () => {
    expect(formatSize(0)).toBe('0 B')
    expect(formatSize(512)).toBe('512 B')
  })

  it('steps up in binary units', () => {
    expect(formatSize(1024)).toBe('1.0 KB')
    expect(formatSize(1024 * 1024)).toBe('1.0 MB')
    expect(formatSize(1024 ** 3)).toBe('1.0 GB')
  })

  it('drops the decimal once the number is large enough to not need it', () => {
    expect(formatSize(20 * 1024)).toBe('20 KB')
  })

  it('refuses to guess at nonsense', () => {
    expect(formatSize(-1)).toBe('-')
    expect(formatSize(Number.NaN)).toBe('-')
  })
})

describe('formatExtension', () => {
  it('uppercases an extension', () => {
    expect(formatExtension('txt')).toBe('TXT')
  })

  it('falls back for a file without one', () => {
    expect(formatExtension('')).toBe('-')
  })
})

describe('pluralize', () => {
  it('keeps a single item singular', () => {
    expect(pluralize(1, 'folder')).toBe('1 folder')
  })

  it('pluralises everything else, zero included', () => {
    expect(pluralize(0, 'folder')).toBe('0 folders')
    expect(pluralize(3, 'file')).toBe('3 files')
  })
})
