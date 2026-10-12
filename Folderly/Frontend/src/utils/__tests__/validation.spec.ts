import { describe, it, expect } from 'vitest'

import {
  validateEmail,
  validateFileName,
  validateFolderName,
  validatePassword,
} from '../validation'

describe('validatePassword', () => {
  it('accepts a password meeting every rule', () => {
    expect(validatePassword('Str0ng!Pass')).toBeNull()
  })

  it.each([
    ['too short', 'Ab1!'],
    ['no uppercase', 'str0ng!pass'],
    ['no lowercase', 'STR0NG!PASS'],
    ['no digit', 'Strong!Pass'],
    ['no special character', 'Str0ngPass'],
  ])('rejects one that is %s', (_reason, password) => {
    expect(validatePassword(password)).not.toBeNull()
  })

  it('reports a missing password rather than failing the pattern', () => {
    expect(validatePassword('')).toBe('Password is required.')
  })
})

describe('validateEmail', () => {
  it('accepts an ordinary address', () => {
    expect(validateEmail('user@folderly.test')).toBeNull()
  })

  it.each(['user', 'user@', '@folderly.test', 'user@folderly'])('rejects %s', (email) => {
    expect(validateEmail(email)).not.toBeNull()
  })
})

describe('validateFolderName', () => {
  it('accepts letters, digits, dashes and underscores', () => {
    expect(validateFolderName('Holiday_photos-2026')).toBeNull()
  })

  it('rejects a dot, which the backend uses to block traversal', () => {
    expect(validateFolderName('..')).not.toBeNull()
    expect(validateFolderName('my.folder')).not.toBeNull()
  })

  it('rejects a slash', () => {
    expect(validateFolderName('a/b')).not.toBeNull()
  })
})

describe('validateFileName', () => {
  it('allows a dot so extensions work', () => {
    expect(validateFileName('report.pdf')).toBeNull()
  })

  it('rejects a name made only of dots', () => {
    expect(validateFileName('..')).not.toBeNull()
  })

  it('rejects a traversal attempt', () => {
    expect(validateFileName('../evil.txt')).not.toBeNull()
  })
})
