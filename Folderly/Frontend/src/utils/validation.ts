// Mirrors of `Folderly/Backend/utils/regexes.py`

export const PASSWORD_PATTERN = /^[^\x00-\x1f\x7f]{8,40}$/

export const PASSWORD_RULE = 'Use between 8 and 40 characters.'

export const FOLDER_NAME_PATTERN = /^[^/\\<>:"|?*\x00-\x1f.]+$/

export const FOLDER_NAME_RULE = 'No dots, slashes, or any of < > : " | ? *'

// Like a folder name, plus dots, but never dots alone.
export const FILE_NAME_PATTERN = /^(?!\.+$)[a-zA-Z0-9_.-]+$/

export const FILE_NAME_RULE = 'Use letters, digits, dots, dashes and underscores only.'

export function validateEmail(email: string): string | null {
  if (!email.trim()) return 'Email is required.'
  // Deliberately loose, an over-strict pattern rejects valid addresses.
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return 'Enter a valid email address.'
  return null
}

export function validatePassword(password: string): string | null {
  if (!password) return 'Password is required.'
  if (!PASSWORD_PATTERN.test(password)) return PASSWORD_RULE
  return null
}

export function validateFolderName(name: string): string | null {
  if (!name.trim()) return 'Name is required.'
  if (!FOLDER_NAME_PATTERN.test(name)) return FOLDER_NAME_RULE
  return null
}

export function validateFileName(name: string): string | null {
  if (!name.trim()) return 'Name is required.'
  if (!FILE_NAME_PATTERN.test(name)) return FILE_NAME_RULE
  return null
}
