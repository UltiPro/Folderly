import { describe, it, expect } from 'vitest'

import {
  fileKind,
  kindLabel,
  previewKind,
  PREVIEW_SIZE_LIMIT,
  TEXT_PREVIEW_SIZE_LIMIT,
} from '../filetypes'

describe('fileKind', () => {
  it('groups the formats people recognise', () => {
    expect(fileKind('pdf')).toBe('pdf')
    expect(fileKind('png')).toBe('image')
    expect(fileKind('xlsx')).toBe('sheet')
    expect(fileKind('docx')).toBe('doc')
    expect(fileKind('zip')).toBe('archive')
    expect(fileKind('ts')).toBe('code')
  })

  it('ignores case, since the extension comes from a filename', () => {
    expect(fileKind('PDF')).toBe('pdf')
    expect(fileKind('JPEG')).toBe('image')
  })

  it('falls back rather than guessing', () => {
    expect(fileKind('')).toBe('other')
    expect(fileKind('wat')).toBe('other')
  })
})

describe('kindLabel', () => {
  it('is the extension itself, upper case', () => {
    expect(kindLabel('pdf')).toBe('PDF')
    expect(kindLabel('xlsx')).toBe('XLSX')
  })

  it('gives up where the badge would overflow or say nothing', () => {
    expect(kindLabel('')).toBeNull()
    expect(kindLabel('sketchbook')).toBeNull()
  })
})

describe('previewKind', () => {
  it('renders images and PDFs', () => {
    expect(previewKind('png', 1000)).toBe('image')
    expect(previewKind('JPG', 1000)).toBe('image')
    expect(previewKind('pdf', 1000)).toBe('pdf')
  })

  it('refuses SVG, which is a document that can carry script', () => {
    expect(previewKind('svg', 1000)).toBeNull()
  })

  it('refuses anything it cannot draw', () => {
    expect(previewKind('docx', 1000)).toBeNull()
    expect(previewKind('', 1000)).toBeNull()
  })

  it('refuses a file too big to hold in memory', () => {
    expect(previewKind('png', PREVIEW_SIZE_LIMIT)).toBe('image')
    expect(previewKind('png', PREVIEW_SIZE_LIMIT + 1)).toBeNull()
  })

  it('reads both textual groups - plain text and source', () => {
    expect(previewKind('txt', 1000)).toBe('text')
    expect(previewKind('md', 1000)).toBe('text')
    expect(previewKind('log', 1000)).toBe('text')
    expect(previewKind('LOG', 1000)).toBe('text')
    expect(previewKind('json', 1000)).toBe('text')
    expect(previewKind('py', 1000)).toBe('text')
  })

  it('shows an uploaded page as its source instead of refusing it', () => {
    expect(previewKind('html', 1000)).toBe('text')
  })

  it('holds text to a ceiling of its own', () => {
    expect(TEXT_PREVIEW_SIZE_LIMIT).toBeLessThan(PREVIEW_SIZE_LIMIT)
    expect(previewKind('txt', TEXT_PREVIEW_SIZE_LIMIT)).toBe('text')
    expect(previewKind('txt', TEXT_PREVIEW_SIZE_LIMIT + 1)).toBeNull()
    expect(previewKind('log', PREVIEW_SIZE_LIMIT)).toBeNull()
  })
})
