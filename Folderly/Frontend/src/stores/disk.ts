import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { fetchDiskUsage } from '@/api/disk'
import type { DiskUsage } from '@/types/api'

export const useDiskStore = defineStore('disk', () => {
  const usage = ref<DiskUsage | null>(null)

  const percentUsed = computed(() => usage.value?.percent_used ?? 0)
  const uploadsBlocked = computed(() => usage.value?.uploads_blocked ?? false)

  // Within 5 points of the cut-off - worth warning about before it bites.
  const nearlyFull = computed(() => {
    if (!usage.value || usage.value.uploads_blocked) return false
    return usage.value.percent_used >= usage.value.limit_percent - 5
  })

  async function refresh(): Promise<void> {
    try {
      usage.value = await fetchDiskUsage()
    } catch {
      // Ambient information, leave the last known value in place.
    }
  }

  function clear(): void {
    usage.value = null
  }

  return { usage, percentUsed, uploadsBlocked, nearlyFull, refresh, clear }
})
