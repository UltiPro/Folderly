import { http } from './client'
import type {
  FolderEntry,
  FolderMember,
  FolderStats,
  Role,
  ShareToken,
  SharedFolder,
  SpacePath,
} from '@/types/api'

// The token is omitted rather than sent empty, an empty `share` is refused.
function target(path: SpacePath, share?: ShareToken) {
  return share ? { path, share } : { path }
}

export async function fetchStats(path: SpacePath, share?: ShareToken): Promise<FolderStats> {
  const { data } = await http.get<FolderStats>('/folder', { params: target(path, share) })
  return data
}

export async function listFolder(path: SpacePath, share?: ShareToken): Promise<FolderEntry[]> {
  const { data } = await http.get<FolderEntry[]>('/folder/list', { params: target(path, share) })
  return data
}

export async function createFolder(path: SpacePath, share?: ShareToken): Promise<void> {
  await http.post('/folder', target(path, share))
}

export async function renameFolder(
  path: SpacePath,
  name: string,
  share?: ShareToken,
): Promise<void> {
  await http.put('/folder', { ...target(path, share), name })
}

export async function deleteFolder(path: SpacePath, share?: ShareToken): Promise<void> {
  await http.delete('/folder', { data: target(path, share) })
}

export async function listSharedWithMe(): Promise<SharedFolder[]> {
  const { data } = await http.get<SharedFolder[]>('/folder/shared')
  return data
}

export async function listMembers(path: SpacePath): Promise<FolderMember[]> {
  const { data } = await http.get<FolderMember[]>('/folder/share', { params: { path } })
  return data
}

export async function shareFolder(path: SpacePath, targetEmail: string, role: Role): Promise<void> {
  await http.post('/folder/share', { path, target_email: targetEmail, role })
}

export async function revokeShare(path: SpacePath, targetEmail: string): Promise<void> {
  await http.delete('/folder/share', { data: { path, target_email: targetEmail } })
}
