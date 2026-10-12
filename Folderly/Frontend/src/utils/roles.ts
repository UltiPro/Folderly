import type { Role } from '@/types/api'

export type Capability = Role | 'owner'

const RANK: Record<Capability, number> = { read: 1, add: 2, edit: 3, owner: 4 }

export function atLeast(held: Capability, needed: Capability): boolean {
  return RANK[held] >= RANK[needed]
}

export const canRead = (held: Capability): boolean => atLeast(held, 'read')

export const canAdd = (held: Capability): boolean => atLeast(held, 'add')

export const canEdit = (held: Capability): boolean => atLeast(held, 'edit')

export const canShare = (held: Capability): boolean => atLeast(held, 'owner')

export function roleLabel(role: Capability): string {
  switch (role) {
    case 'read':
      return 'View only'
    case 'add':
      return 'Can add'
    case 'edit':
      return 'Can edit'
    case 'owner':
      return 'Owner'
  }
}

export function roleDescription(role: Role): string {
  switch (role) {
    case 'read':
      return 'Open the folder and download from it.'
    case 'add':
      return 'Also create folders and upload new files - but not change or delete anything.'
    case 'edit':
      return 'Also overwrite, rename and delete.'
  }
}
