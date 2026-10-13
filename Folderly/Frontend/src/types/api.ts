// Mirrors the backend's schemas (Folderly/Backend/schemas.py), keep in sync.

// A path relative to a space, where `/` is that space's root.
export type SpacePath = string

// Absent or null means the caller's own files.
export type ShareToken = string | null

export interface AuthTokens {
  access_token: string
  refresh_token: string
}

export interface AccessToken {
  access_token: string
}

export interface UserInfo {
  email: string
  active: boolean
}

export interface FolderStats {
  folders: number
  files: number
}

export type FolderEntry = FileEntry | SubfolderEntry

export interface FileEntry {
  name: string
  type: 'file'
  extension: string
  size: number
}

export interface SubfolderEntry {
  name: string
  type: 'folder'
  folders: number
  files: number
}

export function isFileEntry(entry: FolderEntry): entry is FileEntry {
  return entry.type === 'file'
}

export type Role = 'read' | 'add' | 'edit'

export const ROLES: Role[] = ['read', 'add', 'edit']

export interface SharedFolder {
  share: string
  name: string
  owner_email: string
  role: Role
}

export interface FolderMember {
  email: string
  // This share's own role, nothing inherited.
  role: Role
}

export interface FileInfo {
  name: string
  size: number
  // ISO 8601, UTC.
  modified: string
}

export interface DiskUsage {
  total: number
  used: number
  free: number
  percent_used: number
  limit_percent: number
  uploads_blocked: boolean
}

export interface ApiErrorBody {
  code?: number
  status?: string
  message?: string
  errors?: {
    json?: Record<string, string[]>
    query?: Record<string, string[]>
    form?: Record<string, string[]>
  }
}
