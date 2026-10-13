import type { SpacePath } from '@/types/api'

// Slash-separated, no trailing slash. These normalise to that rather than
// trusting input assembled from route params or user typing.

export function segments(path: SpacePath): string[] {
  return path.split('/').filter(Boolean)
}

export function normalize(path: SpacePath): SpacePath {
  const parts = segments(path)
  return parts.length ? `/${parts.join('/')}` : '/'
}

export function basename(path: SpacePath): string {
  const parts = segments(path)
  return parts[parts.length - 1] ?? ''
}

// `/Photos/Vacation` -> `/Photos`, `/Photos` -> `/`, and `/` stays.
export function parent(path: SpacePath): SpacePath {
  const parts = segments(path)
  return parts.length ? `/${parts.slice(0, -1).join('/')}` : '/'
}

export function join(path: SpacePath, name: string): SpacePath {
  const parts = [...segments(path), ...segments(name)]
  return parts.length ? `/${parts.join('/')}` : '/'
}

export interface Crumb {
  label: string
  path: SpacePath
}

export function breadcrumbs(path: SpacePath, rootLabel: string): Crumb[] {
  const crumbs: Crumb[] = [{ label: rootLabel, path: '/' }]
  let walked: SpacePath = '/'
  for (const name of segments(path)) {
    walked = join(walked, name)
    crumbs.push({ label: name, path: walked })
  }
  return crumbs
}
