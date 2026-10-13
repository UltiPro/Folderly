// Mirrors of `Folderly/Backend/utils/regexes.py`

// At least one lower, upper, digit and special character; 8-40 characters.
export const PASSWORD_PATTERN =
  /^(?=.*?[a-z])(?=.*?[A-Z])(?=.*?[0-9])(?=.*?[.~!@#$%^&*()+=[\]\\;:'"/,|{}<>?])[a-zA-Z0-9.~!@#$%^&*()+=[\]\\;:'"/,|{}<>?]{8,40}$/

export const PASSWORD_RULE =
  'Use 8-40 characters with a lowercase letter, an uppercase letter, a digit and a special character.'

export const FOLDER_NAME_PATTERN = /^[a-zA-Z0-9_-]+$/

export const FOLDER_NAME_RULE = 'Use letters, digits, dashes and underscores only.'

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
