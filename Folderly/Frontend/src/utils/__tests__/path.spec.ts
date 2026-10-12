import { describe, it, expect } from 'vitest'

import { basename, breadcrumbs, join, normalize, parent, segments } from '../path'

describe('segments', () => {
  it('splits a path into its parts', () => {
    expect(segments('/Photos/Vacation')).toEqual(['Photos', 'Vacation'])
  })

  it('drops empty parts from sloppy input', () => {
    expect(segments('//Photos//Vacation/')).toEqual(['Photos', 'Vacation'])
  })

  it('returns nothing for the root', () => {
    expect(segments('/')).toEqual([])
  })
})

describe('normalize', () => {
  it('collapses duplicate and trailing slashes', () => {
    expect(normalize('//Photos//Vacation/')).toBe('/Photos/Vacation')
  })

  it('leaves an already-clean path alone', () => {
    expect(normalize('/Photos/Vacation')).toBe('/Photos/Vacation')
  })

  it('represents an empty path as the root', () => {
    expect(normalize('')).toBe('/')
  })
})

describe('basename', () => {
  it('returns the last segment', () => {
    expect(basename('/Photos/Vacation')).toBe('Vacation')
  })

  it('returns the only segment of a top-level folder', () => {
    expect(basename('/Photos')).toBe('Photos')
  })

  it('is empty at the root', () => {
    expect(basename('/')).toBe('')
  })
})

describe('parent', () => {
  it('drops the last segment', () => {
    expect(parent('/Photos/Vacation')).toBe('/Photos')
  })

  it('walks from a top-level folder up to the root of the space', () => {
    expect(parent('/Photos')).toBe('/')
  })

  it('stops at the root, which has nothing above it', () => {
    expect(parent('/')).toBe('/')
  })

  it('normalises while walking up', () => {
    expect(parent('/Photos//Vacation/')).toBe('/Photos')
  })
})

describe('join', () => {
  it('appends a segment', () => {
    expect(join('/Photos', 'Vacation')).toBe('/Photos/Vacation')
  })

  it('does not double up slashes', () => {
    expect(join('/Photos/', '/Vacation')).toBe('/Photos/Vacation')
  })

  it('builds a path from the root', () => {
    expect(join('/', 'Photos')).toBe('/Photos')
  })

  it('appends a whole relative path, as a folder upload does', () => {
    expect(join('/Photos', 'Trip/Day1')).toBe('/Photos/Trip/Day1')
  })
})

describe('breadcrumbs', () => {
  it('starts at the labelled root and walks down', () => {
    expect(breadcrumbs('/Photos/Vacation', 'My files')).toEqual([
      { label: 'My files', path: '/' },
      { label: 'Photos', path: '/Photos' },
      { label: 'Vacation', path: '/Photos/Vacation' },
    ])
  })

  it('is just the root when sitting at the root', () => {
    expect(breadcrumbs('/', 'My files')).toEqual([{ label: 'My files', path: '/' }])
  })

  it('labels the root with the shared folder name in someone elses space', () => {
    expect(breadcrumbs('/Vacation', 'Photos')).toEqual([
      { label: 'Photos', path: '/' },
      { label: 'Vacation', path: '/Vacation' },
    ])
  })
})
