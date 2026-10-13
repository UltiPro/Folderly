export interface DroppedFile {
  file: File
  // Folders above the file, e.g. `Photos/Vacation`, empty when dropped flat.
  relativeDir: string
}

function isFile(entry: FileSystemEntry): entry is FileSystemFileEntry {
  return entry.isFile
}

function isDirectory(entry: FileSystemEntry): entry is FileSystemDirectoryEntry {
  return entry.isDirectory
}

function readFile(entry: FileSystemFileEntry): Promise<File | null> {
  return new Promise((resolve) => {
    entry.file(resolve, () => resolve(null))
  })
}

// `readEntries` returns at most 100 entries at a time, so it has to be called
// until it returns none, one call silently truncates a large folder.
function readDirectory(entry: FileSystemDirectoryEntry): Promise<FileSystemEntry[]> {
  const reader = entry.createReader()

  return new Promise((resolve) => {
    const all: FileSystemEntry[] = []
    const readBatch = () => {
      reader.readEntries(
        (batch) => {
          if (!batch.length) {
            resolve(all)
            return
          }
          all.push(...batch)
          readBatch()
        },
        () => resolve(all),
      )
    }
    readBatch()
  })
}

async function walk(
  entry: FileSystemEntry,
  prefix: string,
  collected: DroppedFile[],
): Promise<void> {
  if (isFile(entry)) {
    const file = await readFile(entry)
    if (file) collected.push({ file, relativeDir: prefix })
    return
  }
  if (!isDirectory(entry)) return

  const nested = prefix ? `${prefix}/${entry.name}` : entry.name
  for (const child of await readDirectory(entry)) {
    await walk(child, nested, collected)
  }
}

export async function readDroppedFiles(transfer: DataTransfer | null): Promise<DroppedFile[]> {
  if (!transfer) return []

  const entries = Array.from(transfer.items)
    .map((item) => item.webkitGetAsEntry())
    .filter((entry): entry is FileSystemEntry => entry !== null)

  // No entry API, an older browser, or a drop of something else entirely.
  // Fall back to the plain file list, which handles everything but folders.
  if (!entries.length) {
    return Array.from(transfer.files).map((file) => ({ file, relativeDir: '' }))
  }

  const collected: DroppedFile[] = []
  for (const entry of entries) {
    await walk(entry, '', collected)
  }
  return collected
}

// The folders above a file chosen through `<input webkitdirectory>`.
export function relativeDirOf(file: File): string {
  const path = (file as File & { webkitRelativePath?: string }).webkitRelativePath
  if (!path) return ''
  return path.split('/').slice(0, -1).join('/')
}
