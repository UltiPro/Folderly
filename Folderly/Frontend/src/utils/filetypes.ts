// Judged from the extension alone

export type FileKind =
  | 'pdf'
  | 'image'
  | 'video'
  | 'audio'
  | 'archive'
  | 'doc'
  | 'sheet'
  | 'slides'
  | 'code'
  | 'text'
  | 'other'

const EXTENSIONS: Record<Exclude<FileKind, 'other'>, readonly string[]> = {
  pdf: ['pdf'],
  image: ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp', 'avif', 'heic', 'ico'],
  video: ['mp4', 'mov', 'avi', 'mkv', 'webm', 'm4v', 'mpg'],
  audio: ['mp3', 'wav', 'flac', 'ogg', 'm4a', 'aac'],
  archive: ['zip', 'rar', '7z', 'tar', 'gz', 'bz2', 'xz'],
  doc: ['doc', 'docx', 'odt', 'rtf'],
  sheet: ['xls', 'xlsx', 'csv', 'tsv', 'ods'],
  slides: ['ppt', 'pptx', 'odp'],
  // prettier-ignore
  code: [
    'js', 'ts', 'jsx', 'tsx', 'vue', 'py', 'java', 'c', 'cpp', 'cs', 'go', 'rs',
    'rb', 'php', 'html', 'css', 'scss', 'json', 'xml', 'yml', 'yaml', 'toml',
    'sh', 'ps1', 'sql',
  ],
  text: ['txt', 'md', 'log', 'ini', 'cfg'],
}

const BY_EXTENSION = new Map<string, FileKind>()
for (const [kind, extensions] of Object.entries(EXTENSIONS)) {
  for (const extension of extensions) BY_EXTENSION.set(extension, kind as FileKind)
}

export function fileKind(extension: string): FileKind {
  return BY_EXTENSION.get(extension.toLowerCase()) ?? 'other'
}

const TONES: Record<FileKind, string> = {
  pdf: 'bg-red-100 text-red-700 dark:bg-red-500/15 dark:text-red-300',
  image: 'bg-violet-100 text-violet-700 dark:bg-violet-500/15 dark:text-violet-300',
  video: 'bg-fuchsia-100 text-fuchsia-700 dark:bg-fuchsia-500/15 dark:text-fuchsia-300',
  audio: 'bg-cyan-100 text-cyan-700 dark:bg-cyan-500/15 dark:text-cyan-300',
  archive: 'bg-amber-100 text-amber-800 dark:bg-amber-500/15 dark:text-amber-300',
  doc: 'bg-blue-100 text-blue-700 dark:bg-blue-500/15 dark:text-blue-300',
  sheet: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300',
  slides: 'bg-orange-100 text-orange-700 dark:bg-orange-500/15 dark:text-orange-300',
  code: 'bg-slate-800 text-slate-100 dark:bg-slate-200 dark:text-slate-800',
  text: 'bg-slate-200 text-soft dark:bg-slate-600 dark:text-slate-100',
  other: 'bg-surface-sunken text-muted',
}

export function kindTone(kind: FileKind): string {
  return TONES[kind]
}

export function kindLabel(extension: string): string | null {
  const trimmed = extension.trim()
  if (!trimmed || trimmed.length > 4) return null
  return trimmed.toUpperCase()
}

export type PreviewKind = 'image' | 'pdf' | 'text'

// A preview holds the whole file in memory, and a 100 MB one, the upload cap
// would stall with no progress bar to explain it.
export const PREVIEW_SIZE_LIMIT = 25 * 1024 * 1024

// Far lower, because an image that size is one bitmap while 25 MB of log is
// 25 million characters of DOM text and a locked tab.
export const TEXT_PREVIEW_SIZE_LIMIT = 1024 * 1024

// SVG stays out deliberately: it is the one image format that is also a
// document, and a blob URL inherits this origin. Harmless in the <img> this
// list feeds, but one line away from the <iframe> branch, where it would not be.
const PREVIEWABLE_IMAGES = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'avif', 'ico']

function isTextual(normalised: string): boolean {
  const kind = fileKind(normalised)
  return kind === 'text' || kind === 'code'
}

export function previewKind(extension: string, size: number): PreviewKind | null {
  const normalised = extension.toLowerCase()
  // Text first: the 25 MB check below would wave a 5 MB log straight through.
  if (isTextual(normalised)) {
    return size > TEXT_PREVIEW_SIZE_LIMIT ? null : 'text'
  }
  if (size > PREVIEW_SIZE_LIMIT) return null
  if (normalised === 'pdf') return 'pdf'
  return PREVIEWABLE_IMAGES.includes(normalised) ? 'image' : null
}
