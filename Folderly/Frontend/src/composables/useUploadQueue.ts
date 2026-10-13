import { computed, ref } from 'vue'

import { errorMessage } from '@/api/client'
import type { ShareToken, SpacePath } from '@/types/api'

export type UploadStatus = 'waiting' | 'uploading' | 'done' | 'failed'

export interface QueuedFile {
  file: File
  destination: SpacePath
  share: ShareToken
}

export interface UploadItem extends QueuedFile {
  id: number
  name: string
  size: number
  status: UploadStatus
  // 0-100
  progress: number
  error?: string
}

export type Uploader = (item: UploadItem, onProgress: (percent: number) => void) => Promise<void>

export const DEFAULT_CONCURRENCY = 3

export function useUploadQueue(uploader: Uploader, concurrency = DEFAULT_CONCURRENCY) {
  const items = ref<UploadItem[]>([])
  const onDrained = ref<(() => void) | null>(null)

  let running = 0
  let nextId = 0

  const pending = computed(() =>
    items.value.filter((item) => item.status === 'waiting' || item.status === 'uploading'),
  )
  const failed = computed(() => items.value.filter((item) => item.status === 'failed'))
  const done = computed(() => items.value.filter((item) => item.status === 'done'))
  const active = computed(() => pending.value.length > 0)

  const overallProgress = computed(() => {
    const total = items.value.reduce((sum, item) => sum + item.size, 0)
    if (!total) return 0
    const sent = items.value.reduce(
      (sum, item) => sum + (item.size * (item.status === 'done' ? 100 : item.progress)) / 100,
      0,
    )
    return Math.round((sent / total) * 100)
  })

  function enqueue(files: Iterable<QueuedFile>): void {
    for (const queued of files) {
      items.value.push({
        ...queued,
        id: nextId++,
        name: queued.file.name,
        size: queued.file.size,
        status: 'waiting',
        progress: 0,
      })
    }
    pump()
  }

  function pump(): void {
    while (running < concurrency) {
      const next = items.value.find((item) => item.status === 'waiting')
      if (!next) break
      void run(next)
    }
  }

  async function run(item: UploadItem): Promise<void> {
    running += 1
    item.status = 'uploading'
    try {
      await uploader(item, (percent) => {
        item.progress = percent
      })
      item.status = 'done'
      item.progress = 100
    } catch (caught) {
      item.status = 'failed'
      item.error = errorMessage(caught, 'Could not upload this file.')
    } finally {
      running -= 1
      pump()
      if (running === 0 && !items.value.some((entry) => entry.status === 'waiting')) {
        onDrained.value?.()
      }
    }
  }

  function clearFinished(): void {
    items.value = items.value.filter((item) => item.status !== 'done')
  }

  function reset(): void {
    items.value = []
  }

  return {
    items,
    active,
    pending,
    done,
    failed,
    overallProgress,
    onDrained,
    enqueue,
    clearFinished,
    reset,
  }
}
