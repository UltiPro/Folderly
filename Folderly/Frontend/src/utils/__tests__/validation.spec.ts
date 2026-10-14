import { describe, it, expect } from 'vitest'

import {
  validateEmail,
  validateFileName,
  validateFolderName,
  validatePassword,
} from '../validation'

describe('validatePassword', () => {
  it('accepts what a password generator produces', () => {
    expect(validatePassword('Kf8wQ2zPmR4tLv9')).toBeNull()
    expect(validatePassword('long-and-easy-to-remember')).toBeNull()
    expect(validatePassword('has\u0142o z polskimi znakami')).toBeNull()
  })

  it.each([
    ['too short', 'Ab1!'],
    ['too long', 'a'.repeat(41)],
    ['a control character', 'abcdefg\th'],
  ])('rejects one with %s', (_reason, password) => {
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
    expect(validateFolderName('Wakacje 2024')).toBeNull()
    expect(validateFolderName('Zdjęcia (kopia)')).toBeNull()
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
