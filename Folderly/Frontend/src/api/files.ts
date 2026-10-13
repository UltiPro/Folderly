import { http } from './client'
import type { FileInfo, ShareToken, SpacePath } from '@/types/api'

function target(path: SpacePath, filename: string, share?: ShareToken) {
  return share ? { path, filename, share } : { path, filename }
}

export async function fetchFileInfo(
  path: SpacePath,
  filename: string,
  share?: ShareToken,
): Promise<FileInfo> {
  const { data } = await http.get<FileInfo>('/file', { params: target(path, filename, share) })
  return data
}

export interface UploadOptions {
  share?: ShareToken
  onProgress?: (percent: number) => void
  signal?: AbortSignal
}

// The explicit undefined Content-Type lets the browser set its own multipart
// boundary, a hand-written header here produces an unparseable body.
export async function uploadFile(
  path: SpacePath,
  file: File,
  options: UploadOptions = {},
): Promise<void> {
  const body = new FormData()
  body.append('path', path)
  if (options.share) body.append('share', options.share)
  body.append('file', file)

  await http.post('/file', body, {
    headers: { 'Content-Type': undefined },
    signal: options.signal,
    onUploadProgress: (event) => {
      if (options.onProgress && event.total) {
        options.onProgress(Math.round((event.loaded / event.total) * 100))
      }
    },
  })
}

export async function renameFile(
  path: SpacePath,
  filename: string,
  name: string,
  share?: ShareToken,
): Promise<void> {
  await http.put('/file', { ...target(path, filename, share), name })
}

export async function deleteFile(
  path: SpacePath,
  filename: string,
  share?: ShareToken,
): Promise<void> {
  await http.delete('/file', { data: target(path, filename, share) })
}

// The file's bytes, for showing it in the page. Through axios because an
// `<img src>` cannot carry the Authorization header.
export async function fetchFileBlob(
  path: SpacePath,
  filename: string,
  share?: ShareToken,
): Promise<Blob> {
  const response = await http.get('/file/download', {
    params: target(path, filename, share),
    responseType: 'blob',
  })
  return response.data as Blob
}

// Same reason as above, plus: the object URL is revoked once the click fires.
export async function downloadFile(
  path: SpacePath,
  filename: string,
  share?: ShareToken,
): Promise<void> {
  const response = await http.get('/file/download', {
    params: target(path, filename, share),
    responseType: 'blob',
  })

  const url = URL.createObjectURL(response.data as Blob)
  try {
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    link.remove()
  } finally {
    URL.revokeObjectURL(url)
  }
}
