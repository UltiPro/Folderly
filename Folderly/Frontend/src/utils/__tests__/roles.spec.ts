import { describe, it, expect } from 'vitest'

import { atLeast, canAdd, canEdit, canRead, canShare, roleLabel } from '../roles'
import { ROLES } from '@/types/api'

describe('atLeast', () => {
  it('ranks the roles the way the backend does', () => {
    expect(atLeast('add', 'read')).toBe(true)
    expect(atLeast('edit', 'add')).toBe(true)
    expect(atLeast('owner', 'edit')).toBe(true)
  })

  it('does not let a weaker role stand in for a stronger one', () => {
    expect(atLeast('read', 'add')).toBe(false)
    expect(atLeast('add', 'edit')).toBe(false)
    expect(atLeast('edit', 'owner')).toBe(false)
  })

  it('accepts a role as equal to itself', () => {
    for (const role of [...ROLES, 'owner'] as const) {
      expect(atLeast(role, role)).toBe(true)
    }
  })
})

describe('what each role may do', () => {
  it('lets everyone view and download', () => {
    expect([canRead('read'), canRead('add'), canRead('edit'), canRead('owner')]).toEqual([
      true,
      true,
      true,
      true,
    ])
  })

  it('keeps read out of adding', () => {
    expect([canAdd('read'), canAdd('add'), canAdd('edit'), canAdd('owner')]).toEqual([
      false,
      true,
      true,
      true,
    ])
  })

  it('stops add short of changing what is already there', () => {
    expect([canEdit('read'), canEdit('add'), canEdit('edit'), canEdit('owner')]).toEqual([
      false,
      false,
      true,
      true,
    ])
  })

  it('leaves sharing to the owner alone', () => {
    expect([canShare('read'), canShare('add'), canShare('edit'), canShare('owner')]).toEqual([
      false,
      false,
      false,
      true,
    ])
  })
})

describe('roleLabel', () => {
  it('gives every role something to render', () => {
    for (const role of [...ROLES, 'owner'] as const) {
      expect(roleLabel(role)).toBeTruthy()
    }
  })
})
