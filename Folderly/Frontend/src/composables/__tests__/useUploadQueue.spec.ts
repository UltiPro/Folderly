import { describe, it, expect, vi } from 'vitest'
import { nextTick } from 'vue'

import { useUploadQueue, type QueuedFile, type UploadItem } from '../useUploadQueue'

function queued(name: string, size = 100): QueuedFile {
  return {
    file: new File(['x'.repeat(size)], name),
    destination: '/',
    share: null,
  }
}

function deferred() {
  let resolve!: () => void
  let reject!: (reason: Error) => void
  const promise = new Promise<void>((res, rej) => {
    resolve = res
    reject = rej
  })
  return { promise, resolve, reject }
}

async function settle() {
  for (let i = 0; i < 20; i += 1) await nextTick()
}

describe('useUploadQueue', () => {
  it('uploads every file in the batch', async () => {
    const uploader = vi.fn<() => Promise<void>>().mockResolvedValue(undefined)
    const queue = useUploadQueue(uploader)

    queue.enqueue([queued('a.txt'), queued('b.txt'), queued('c.txt')])
    await settle()

    expect(uploader).toHaveBeenCalledTimes(3)
    expect(queue.done.value.map((item) => item.name)).toEqual(['a.txt', 'b.txt', 'c.txt'])
    expect(queue.active.value).toBe(false)
  })

  it('keeps no more than the concurrency limit in flight', async () => {
    let inFlight = 0
    let peak = 0
    const gates: ReturnType<typeof deferred>[] = []

    const queue = useUploadQueue(() => {
      inFlight += 1
      peak = Math.max(peak, inFlight)
      const gate = deferred()
      gates.push(gate)
      return gate.promise.finally(() => {
        inFlight -= 1
      })
    }, 3)

    queue.enqueue(Array.from({ length: 8 }, (_, index) => queued(`file-${index}.txt`)))
    await settle()

    expect(peak).toBe(3)
    expect(queue.items.value.filter((item) => item.status === 'uploading')).toHaveLength(3)
    expect(queue.items.value.filter((item) => item.status === 'waiting')).toHaveLength(5)

    for (let wave = 0; wave < 10 && queue.done.value.length < 8; wave += 1) {
      for (const gate of gates) gate.resolve()
      await settle()
    }

    expect(peak).toBe(3)
    expect(queue.done.value).toHaveLength(8)
  })

  it('carries on after a file fails, and keeps its message', async () => {
    const queue = useUploadQueue((item: UploadItem) =>
      item.name === 'bad.txt' ? Promise.reject(new Error('nope')) : Promise.resolve(undefined),
    )

    queue.enqueue([queued('good.txt'), queued('bad.txt'), queued('also-good.txt')])
    await settle()

    expect(queue.done.value.map((item) => item.name)).toEqual(['good.txt', 'also-good.txt'])
    expect(queue.failed.value).toHaveLength(1)
    const [failure] = queue.failed.value
    expect(failure?.name).toBe('bad.txt')
    expect(failure?.error).toBeTruthy()
  })

  it('weights overall progress by size, so a big file is not one third of three', async () => {
    const gate = deferred()
    const queue = useUploadQueue((item, onProgress) => {
      if (item.name === 'big.bin') {
        onProgress(50)
        return gate.promise
      }
      return Promise.resolve(undefined)
    })

    queue.enqueue([queued('big.bin', 800), queued('small.txt', 200)])
    await settle()

    // 800 bytes half sent plus 200 done = 600 of 1000.
    expect(queue.overallProgress.value).toBe(60)

    gate.resolve()
    await settle()
    expect(queue.overallProgress.value).toBe(100)
  })

  it('announces completion once, after the last file settles', async () => {
    const drained = vi.fn<() => void>()
    const queue = useUploadQueue(() => Promise.resolve(undefined))
    queue.onDrained.value = drained

    queue.enqueue([queued('a.txt'), queued('b.txt'), queued('c.txt'), queued('d.txt')])
    await settle()

    expect(drained).toHaveBeenCalledTimes(1)
  })

  it('keeps failures when the finished rows are cleared', async () => {
    const queue = useUploadQueue((item: UploadItem) =>
      item.name === 'bad.txt' ? Promise.reject(new Error('nope')) : Promise.resolve(undefined),
    )

    queue.enqueue([queued('good.txt'), queued('bad.txt')])
    await settle()
    queue.clearFinished()

    expect(queue.items.value.map((item) => item.name)).toEqual(['bad.txt'])
  })

  it('remembers where each file was going, not where the user is now', async () => {
    const seen: string[] = []
    const queue = useUploadQueue((item) => {
      seen.push(`${item.destination}:${item.name}`)
      return Promise.resolve(undefined)
    })

    queue.enqueue([
      { ...queued('a.txt'), destination: '/Photos' },
      { ...queued('b.txt'), destination: '/Photos/Trip' },
    ])
    await settle()

    expect(seen).toEqual(['/Photos:a.txt', '/Photos/Trip:b.txt'])
  })
})
